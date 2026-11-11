"""Spike C: LLM Function Calling & Offline Replay Stub (Chunk P04).

Validates:
1. Official `google-genai` SDK (`>=2.30.1`, verified `3.1.0`) Interactions API tool calling shape
   with model `gemini-3.8-flash` (configurable via `LLM_MODEL`) and `HttpOptions(timeout=20_000)`.
2. One stub tool `get_value(area)` returning a deterministic harmonized fire count.
3. Offline `replay` mode (`LLM_PROVIDER=replay`) requiring zero network calls.
4. Grounding check ensuring every 2+ digit number in the answer comes strictly from tool outputs.
"""

from __future__ import annotations

import json
import os
import re
import time
from typing import Any

STUB_AREA_VALUES: dict[str, dict[str, Any]] = {
    "PRESET-CHT": {
        "area_id": "PRESET-CHT",
        "year": 2025,
        "harmonized_events": 384,
        "season": "Mar-May",
    },
    "BGD": {
        "area_id": "BGD",
        "year": 2025,
        "harmonized_events": 562,
        "season": "Mar-May",
    },
}

GET_VALUE_DECLARATION: dict[str, Any] = {
    "type": "function",
    "name": "get_value",
    "description": "Return harmonized MODIS-equivalent fire event count and peak season for an area.",
    "parameters": {
        "type": "object",
        "properties": {
            "area": {
                "type": "string",
                "description": "Region ID such as PRESET-CHT or BGD",
            }
        },
        "required": ["area"],
    },
}

SYSTEM_INSTRUCTION = (
    "You are PyroScope. Answer using ONLY numbers returned by tools. "
    "Never invent or estimate numbers. State the harmonized event count and year."
)


def get_value(area: str) -> dict[str, Any]:
    """Typed tool returning deterministic harmonized fire metrics for `area`."""
    return STUB_AREA_VALUES.get(area, STUB_AREA_VALUES["PRESET-CHT"])


def verify_grounding(answer: str, tool_outputs: list[dict[str, Any]]) -> bool:
    """Verify every 2+ digit number in `answer` appears in `tool_outputs`."""
    allowed_text = json.dumps(tool_outputs)
    numbers_in_answer = re.findall(r"\b\d{2,}\b", answer)
    return all(num in allowed_text for num in numbers_in_answer)


def ask_replay(question: str, area: str = "PRESET-CHT") -> dict[str, Any]:
    """Zero-network deterministic replay mode calling `get_value(area)`."""
    t0 = time.perf_counter()
    result = get_value(area)
    duration_ms = round((time.perf_counter() - t0) * 1000.0, 3)
    answer = (
        f"In {result['year']}, {result['area_id']} recorded {result['harmonized_events']} "
        f"harmonized MODIS-equivalent fire events (peak season: {result['season']})."
    )
    assert verify_grounding(answer, [result]), "Replay answer failed grounding check"
    return {
        "mode": "replay",
        "question": question,
        "answer": answer,
        "toolCalls": [
            {"name": "get_value", "args": {"area": area}, "durationMs": duration_ms}
        ],
        "grounded": True,
    }


def ask_gemini_live(
    question: str, client: Any = None, model: str | None = None
) -> dict[str, Any]:
    """Call Gemini Interactions API with `get_value` tool and 20s timeout."""
    model_id = model or os.environ.get("LLM_MODEL", "gemini-3.8-flash")
    if client is None:
        from google import genai
        from google.genai import types

        client = genai.Client(
            api_key=os.environ["GEMINI_API_KEY"],
            http_options=types.HttpOptions(timeout=20_000),
        )

    interaction = client.interactions.create(
        model=model_id,
        system_instruction=SYSTEM_INSTRUCTION,
        input=question,
        tools=[GET_VALUE_DECLARATION],
    )
    tool_calls: list[dict[str, Any]] = []
    tool_outputs: list[dict[str, Any]] = []
    function_results: list[dict[str, Any]] = []

    for step in interaction.steps:
        if getattr(step, "type", None) == "function_call" and step.name == "get_value":
            t0 = time.perf_counter()
            area_arg = str(step.arguments.get("area", "PRESET-CHT"))
            res = get_value(area_arg)
            dur_ms = round((time.perf_counter() - t0) * 1000.0, 3)
            tool_calls.append(
                {"name": step.name, "args": {"area": area_arg}, "durationMs": dur_ms}
            )
            tool_outputs.append(res)
            function_results.append(
                {
                    "type": "function_result",
                    "name": step.name,
                    "call_id": step.id,
                    "result": [{"type": "text", "text": json.dumps(res)}],
                }
            )

    final_turn = client.interactions.create(
        model=model_id,
        system_instruction=SYSTEM_INSTRUCTION,
        input=function_results,
        tools=[GET_VALUE_DECLARATION],
        previous_interaction_id=interaction.id,
    )
    answer = str(final_turn.output_text)
    grounded = verify_grounding(answer, tool_outputs)
    return {
        "mode": "live",
        "model": model_id,
        "answer": answer,
        "toolCalls": tool_calls,
        "grounded": grounded,
    }


if __name__ == "__main__":
    q = "How many harmonized fire events occurred in PRESET-CHT in 2025?"
    replay_resp = ask_replay(q, "PRESET-CHT")
    print("Spike C (replay):", json.dumps(replay_resp, indent=2))
