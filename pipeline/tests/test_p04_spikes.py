"""Unit tests for P04 technical spikes (DuckDB Parquet UINT64, LLM tools & replay, SPIKE_RESULTS)."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import duckdb
import h3
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

REPO_ROOT = Path(__file__).parents[2]


def _load_module(name: str, rel_path: str) -> Any:
    path = REPO_ROOT / rel_path
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_spike_b_uint64_parquet_duckdb_roundtrip(tmp_path: Path) -> None:
    """Verify UINT64 H3 preservation across pandas -> Parquet -> DuckDB -> hex and INT16 cast."""
    cell_hex = h3.latlng_to_cell(23.685, 90.3563, 7)
    cell_u64 = np.uint64(int(cell_hex, 16))
    df = pd.DataFrame(
        {
            "h3_r7": np.array([cell_u64, cell_u64], dtype=np.uint64),
            "year": np.array([2020, 2021], dtype=np.int16),
            "month": np.array([3, 4], dtype=np.int8),
            "event_count": np.array([10, 20], dtype=np.int32),
        }
    )
    pq_path = tmp_path / "test_cell.parquet"
    pq.write_table(pa.Table.from_pandas(df, preserve_index=False), pq_path, compression="ZSTD")

    con = duckdb.connect(":memory:")
    col_type = con.execute("DESCRIBE SELECT h3_r7 FROM read_parquet(?)", [str(pq_path)]).fetchone()
    assert col_type is not None and col_type[1] == "UBIGINT"

    row = con.execute(
        """
        SELECT h3_r7, SUM(event_count)
        FROM read_parquet(?)
        WHERE (CAST(year AS INTEGER) * 100 + month) BETWEEN 202001 AND 202112
        GROUP BY h3_r7
        """,
        [str(pq_path)],
    ).fetchone()
    con.close()

    assert row is not None
    recovered_hex = format(int(row[0]), "x")
    assert recovered_hex == cell_hex
    assert len(recovered_hex) == 15
    assert h3.is_valid_cell(recovered_hex)
    assert int(row[1]) == 30


def test_spike_c_replay_and_mocked_live_tool_calling() -> None:
    """Verify Spike C replay mode, mocked Gemini Interactions API tool turn, and grounding check."""
    spike_c = _load_module("spike_c", "spikes/spike_c_llm_tools/run_spike.py")

    replay = spike_c.ask_replay("How many fires in PRESET-CHT?", "PRESET-CHT")
    assert replay["mode"] == "replay"
    assert replay["grounded"] is True
    assert "384" in replay["answer"]
    assert replay["toolCalls"][0]["name"] == "get_value"

    class MockInteractions:
        def __init__(self) -> None:
            self.calls = 0

        def create(self, **kwargs: Any) -> Any:
            self.calls += 1
            if self.calls == 1:
                return SimpleNamespace(
                    id="inter_123",
                    steps=[
                        SimpleNamespace(
                            type="function_call",
                            id="call_1",
                            name="get_value",
                            arguments={"area": "PRESET-CHT"},
                        )
                    ],
                )
            assert kwargs.get("previous_interaction_id") == "inter_123"
            return SimpleNamespace(
                id="inter_124",
                steps=[],
                output_text="In 2025, PRESET-CHT had 384 harmonized fire events.",
            )

    mock_client = SimpleNamespace(interactions=MockInteractions())
    live = spike_c.ask_gemini_live("How many fires in PRESET-CHT?", client=mock_client)
    assert live["mode"] == "live"
    assert live["model"] == "gemini-3.8-flash"
    assert live["grounded"] is True
    assert "384" in live["answer"]
    assert len(live["toolCalls"]) == 1

    # Verify hallucinated number fails grounding check
    assert (
        spike_c.verify_grounding("There were 999 fires in 2025.", [{"year": 2025, "count": 384}])
        is False
    )


def test_spike_results_doc_exists() -> None:
    doc_path = REPO_ROOT / "docs" / "SPIKE_RESULTS.md"
    assert doc_path.exists()
    content = doc_path.read_text(encoding="utf-8")
    assert "Spike A" in content
    assert "Spike B" in content
    assert "Spike C" in content
    assert "gemini-3.8-flash" in content
