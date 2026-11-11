"""Tool registry and execution dispatcher for Ask PyroScope."""

from __future__ import annotations

import time
from typing import Any

import duckdb

from app.core.dataset import LoadedDataset
from app.features.ask.schemas import Citation, ToolCallLog
from app.features.ask.tools.compare_years import CompareYearsInput, execute_compare_years
from app.features.ask.tools.get_anomalies import GetAnomaliesInput, execute_get_anomalies
from app.features.ask.tools.get_calendar import GetCalendarInput, execute_get_calendar
from app.features.ask.tools.get_season import GetSeasonInput, execute_get_season
from app.features.ask.tools.get_yearly_stats import GetYearlyStatsInput, execute_get_yearly_stats
from app.features.ask.tools.list_areas import ListAreasInput, execute_list_areas

TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "type": "function",
        "name": "list_areas",
        "description": "List available districts, divisions, and presets with region IDs.",
        "parameters": {
            "type": "object",
            "properties": {
                "level": {
                    "type": "string",
                    "enum": ["country", "adm1", "adm2", "preset"],
                    "description": "Optional administrative hierarchy level filter",
                }
            },
        },
    },
    {
        "type": "function",
        "name": "get_season",
        "description": "Get normal fire season parameters (start month, peak month, end month, share of annual burning) for an area.",
        "parameters": {
            "type": "object",
            "properties": {
                "area_id": {
                    "type": "string",
                    "description": "Canonical area ID such as 'PRESET-CHT' or 'BGD-ADM2-rangamati'",
                }
            },
            "required": ["area_id"],
        },
    },
    {
        "type": "function",
        "name": "get_calendar",
        "description": "Get monthly fire calendar grid values, anomaly classifications, and baseline climatology for an area.",
        "parameters": {
            "type": "object",
            "properties": {
                "area_id": {"type": "string", "description": "Canonical area ID"},
                "year": {"type": "integer", "description": "Optional single year filter"},
            },
            "required": ["area_id"],
        },
    },
    {
        "type": "function",
        "name": "get_yearly_stats",
        "description": "Get yearly total harmonized fire event counts, FRP, historical rank, and anomaly vs mean for an area.",
        "parameters": {
            "type": "object",
            "properties": {
                "area_id": {"type": "string", "description": "Canonical area ID"},
                "year": {"type": "integer", "description": "Optional single year filter"},
            },
            "required": ["area_id"],
        },
    },
    {
        "type": "function",
        "name": "get_anomalies",
        "description": "Get months flagged as 'normal', 'elevated', or 'extreme' based on historical baseline percentiles.",
        "parameters": {
            "type": "object",
            "properties": {
                "area_id": {"type": "string", "description": "Canonical area ID"},
                "year": {"type": "integer", "description": "Optional single year filter"},
            },
            "required": ["area_id"],
        },
    },
    {
        "type": "function",
        "name": "compare_years",
        "description": "Compare fire counts, peak months, and annual ratio between two years for an area.",
        "parameters": {
            "type": "object",
            "properties": {
                "area_id": {"type": "string", "description": "Canonical area ID"},
                "year_a": {"type": "integer", "description": "Baseline year (e.g. 2019)"},
                "year_b": {"type": "integer", "description": "Comparison year (e.g. 2020)"},
            },
            "required": ["area_id", "year_a", "year_b"],
        },
    },
]


def dispatch_tool(
    name: str,
    args: dict[str, Any],
    dataset: LoadedDataset,
    cursor: duckdb.DuckDBPyConnection,
) -> tuple[dict[str, Any], Citation, ToolCallLog]:
    """Execute named tool with validated arguments, returning result dict, citation, and audit log."""
    t0 = time.perf_counter()

    if name == "list_areas":
        parsed_la = ListAreasInput(**args)
        result = execute_list_areas(dataset, cursor, level=parsed_la.level)
    elif name == "get_season":
        parsed_gs = GetSeasonInput(**args)
        result = execute_get_season(dataset, cursor, area_id=parsed_gs.area_id)
    elif name == "get_calendar":
        parsed_gc = GetCalendarInput(**args)
        result = execute_get_calendar(dataset, cursor, area_id=parsed_gc.area_id, year=parsed_gc.year)
    elif name == "get_yearly_stats":
        parsed_ys = GetYearlyStatsInput(**args)
        result = execute_get_yearly_stats(dataset, cursor, area_id=parsed_ys.area_id, year=parsed_ys.year)
    elif name == "get_anomalies":
        parsed_ga = GetAnomaliesInput(**args)
        result = execute_get_anomalies(dataset, cursor, area_id=parsed_ga.area_id, year=parsed_ga.year)
    elif name == "compare_years":
        parsed_cy = CompareYearsInput(**args)
        result = execute_compare_years(
            dataset, cursor, area_id=parsed_cy.area_id, year_a=parsed_cy.year_a, year_b=parsed_cy.year_b
        )
    else:
        raise ValueError(f"Unknown tool '{name}'")

    duration_ms = round((time.perf_counter() - t0) * 1000.0, 2)
    ev = result.get("evidence", {})
    citation = Citation(
        tool=ev.get("tool", name),
        areaId=ev.get("areaId"),
        years=ev.get("years", []),
        dataVersion=ev.get("dataVersion", dataset.data_version),
    )
    log = ToolCallLog(name=name, args=args, durationMs=duration_ms)
    return result, citation, log
