"""Deterministic area alias resolution using RapidFuzz matching against region catalog."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd
from rapidfuzz import fuzz, process

from app.core.config import settings


@dataclass(frozen=True)
class AreaResolutionResult:
    """Result of area resolution from user natural language or query."""

    resolved: bool
    area_id: str | None = None
    canonical_name: str | None = None
    matched_term: str | None = None
    score: float = 0.0
    clarification: str | None = None
    candidates: list[tuple[str, str]] = field(default_factory=list)


def load_region_lookup(
    reference_dir: str | Path | None = None,
    data_dir: str | Path | None = None,
) -> tuple[dict[str, str], dict[str, str]]:
    """Build lowercase search term -> region_id and region_id -> canonical_name lookups."""
    ref_path = Path(reference_dir or settings.reference_dir) / "regions.parquet"
    data_path = Path(data_dir or settings.data_dir) / "regions.parquet"

    term_to_id: dict[str, str] = {}
    id_to_name: dict[str, str] = {}

    for path in (data_path, ref_path):
        if not path.exists():
            continue
        df = pd.read_parquet(path)
        for _, row in df.iterrows():
            rid = str(row["region_id"])
            name = str(row["name"])
            id_to_name[rid] = name

            # Map region_id and name
            term_to_id[rid.lower()] = rid
            term_to_id[name.lower()] = rid

            # Map aliases
            aliases = row.get("aliases")
            if aliases is not None and hasattr(aliases, "__iter__") and not isinstance(aliases, (str, bytes)):
                for alias in aliases:
                    term_to_id[str(alias).strip().lower()] = rid

    return term_to_id, id_to_name


def resolve_area_name(
    query: str,
    reference_dir: str | Path | None = None,
    data_dir: str | Path | None = None,
    score_threshold: float = 85.0,
) -> AreaResolutionResult:
    """Resolve a user-provided area name or query fragment to a canonical region_id."""
    clean_query = query.strip()
    if not clean_query:
        return AreaResolutionResult(
            resolved=False,
            clarification="No area was specified. Please provide a region name (e.g. 'Chittagong Hill Tracts', 'Rangamati', or 'Dhaka').",
        )

    term_to_id, id_to_name = load_region_lookup(reference_dir, data_dir)
    lower_q = clean_query.lower()

    # 1. Exact match fast path
    if lower_q in term_to_id:
        rid = term_to_id[lower_q]
        return AreaResolutionResult(
            resolved=True,
            area_id=rid,
            canonical_name=id_to_name.get(rid, rid),
            matched_term=lower_q,
            score=100.0,
        )

    # 2. Fuzzy match using RapidFuzz ratio
    extract_matches = process.extract(
        lower_q,
        term_to_id.keys(),
        scorer=fuzz.ratio,
        limit=3,
    )

    if not extract_matches:
        return AreaResolutionResult(
            resolved=False,
            clarification=f"Could not identify area '{clean_query}'. Please select a valid district or preset.",
        )

    best_term, best_score, _ = extract_matches[0]
    if best_score >= score_threshold:
        rid = term_to_id[best_term]
        return AreaResolutionResult(
            resolved=True,
            area_id=rid,
            canonical_name=id_to_name.get(rid, rid),
            matched_term=best_term,
            score=float(best_score),
        )

    # Below threshold: construct clarifying message listing up to 3 candidate areas
    seen_ids: set[str] = set()
    candidate_list: list[tuple[str, str]] = []
    for term, score, _ in extract_matches:
        c_id = term_to_id[term]
        if c_id not in seen_ids:
            seen_ids.add(c_id)
            candidate_list.append((c_id, id_to_name.get(c_id, c_id)))

    candidate_str = ", ".join(f"'{name}' ({cid})" for cid, name in candidate_list)
    clarification = (
        f"I could not identify area '{clean_query}'. Did you mean: {candidate_str}? "
        f"Please clarify which area you would like to analyze."
    )
    return AreaResolutionResult(
        resolved=False,
        score=float(best_score),
        clarification=clarification,
        candidates=candidate_list,
    )
