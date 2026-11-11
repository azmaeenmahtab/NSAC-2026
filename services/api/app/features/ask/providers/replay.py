"""Offline deterministic replay provider for Ask PyroScope demos and testing."""

from __future__ import annotations

import re
from typing import Any

import duckdb

from app.core.dataset import LoadedDataset
from app.features.ask.grounding import verify_grounding
from app.features.ask.providers.base import BaseLLMProvider
from app.features.ask.resolve_area import resolve_area_name
from app.features.ask.schemas import AskResponse, Citation, ToolCallLog
from app.features.ask.tools.registry import dispatch_tool

MONTH_NAMES = {
    1: "January", 2: "February", 3: "March", 4: "April",
    5: "May", 6: "June", 7: "July", 8: "August",
    9: "September", 10: "October", 11: "November", 12: "December",
}


class ReplayProvider(BaseLLMProvider):
    """Deterministic, zero-network LLM provider driven by real tool executions."""

    async def ask(
        self,
        question: str,
        area_id: str | None,
        style: str,
        dataset: LoadedDataset,
        cursor: duckdb.DuckDBPyConnection,
    ) -> AskResponse:
        """Execute deterministic replay matching question intent to tools and templated text."""
        # 1. Resolve target area
        target_area = area_id
        canonical_name = area_id or "Bangladesh"

        if not target_area:
            res = resolve_area_name(question, data_dir=dataset.data_dir)
            if res.resolved and res.area_id:
                target_area = res.area_id
                canonical_name = res.canonical_name or res.area_id
            elif res.clarification:
                return AskResponse(
                    answer=res.clarification,
                    citations=[],
                    toolCalls=[],
                    mode="replay",
                )
            else:
                target_area = "PRESET-CHT"
                canonical_name = "Chittagong Hill Tracts"

        # 2. Extract years from question if present
        found_years = [int(y) for y in re.findall(r"\b(19\d\d|20\d\d)\b", question)]
        target_year = found_years[0] if found_years else 2020

        lower_q = question.lower()
        tool_results: list[dict[str, Any]] = []
        citations: list[Citation] = []
        tool_logs: list[ToolCallLog] = []

        # 3. Intent dispatch
        if ("season" in lower_q or "start" in lower_q) and ("unusual" in lower_q or "anomaly" in lower_q):
            # Combined Season + Anomaly
            res_s, cit_s, log_s = dispatch_tool("get_season", {"area_id": target_area}, dataset, cursor)
            tool_results.append(res_s)
            citations.append(cit_s)
            tool_logs.append(log_s)

            res_a, cit_a, log_a = dispatch_tool(
                "get_anomalies", {"area_id": target_area, "year": target_year}, dataset, cursor
            )
            tool_results.append(res_a)
            citations.append(cit_a)
            tool_logs.append(log_a)

            start_m = res_s["start_month"]
            peak_m = res_s["peak_month"]
            end_m = res_s["end_month"]
            share_pct = round(res_s["share_of_annual"] * 100.0, 1)

            # Analyze anomalies for target_year
            anom_list = res_a.get("anomalies", [])
            extreme_months = [MONTH_NAMES.get(a["month"], str(a["month"])) for a in anom_list if a["class"] == "extreme"]
            elevated_months = [MONTH_NAMES.get(a["month"], str(a["month"])) for a in anom_list if a["class"] == "elevated"]

            if extreme_months:
                anom_text = f"{target_year} had an extreme month ({', '.join(extreme_months)})"
            elif elevated_months:
                anom_text = f"{target_year} had an elevated month ({', '.join(elevated_months)})"
            else:
                anom_text = f"{target_year} burning activity remained within normal historical levels"

            answer = (
                f"In {canonical_name}, the normal fire season starts in month {start_m} ({MONTH_NAMES.get(start_m)}) "
                f"and peaks in month {peak_m} ({MONTH_NAMES.get(peak_m)}), running through month {end_m} ({MONTH_NAMES.get(end_m)}), "
                f"accounting for {share_pct}% of annual activity. In {target_year}, {anom_text}. "
                f"(Data version: {dataset.data_version})."
            )

        elif "compare" in lower_q or ("vs" in lower_q and len(found_years) >= 2):
            yr_a = found_years[0] if len(found_years) >= 1 else 2019
            yr_b = found_years[1] if len(found_years) >= 2 else 2020
            res_c, cit_c, log_c = dispatch_tool(
                "compare_years", {"area_id": target_area, "year_a": yr_a, "year_b": yr_b}, dataset, cursor
            )
            tool_results.append(res_c)
            citations.append(cit_c)
            tool_logs.append(log_c)

            tot_a = res_c["year_a"]["harmonized_total"]
            tot_b = res_c["year_b"]["harmonized_total"]
            ratio = res_c.get("ratio_b_to_a")
            answer = (
                f"Comparing fire events in {canonical_name}: {yr_a} recorded {tot_a} events, while {yr_b} recorded "
                f"{tot_b} events (ratio: {ratio}x). (Data version: {dataset.data_version})."
            )

        elif "season" in lower_q or "peak" in lower_q or "start" in lower_q or "when" in lower_q:
            res_s, cit_s, log_s = dispatch_tool("get_season", {"area_id": target_area}, dataset, cursor)
            tool_results.append(res_s)
            citations.append(cit_s)
            tool_logs.append(log_s)

            start_m = res_s["start_month"]
            peak_m = res_s["peak_month"]
            end_m = res_s["end_month"]
            share_pct = round(res_s["share_of_annual"] * 100.0, 1)

            answer = (
                f"In {canonical_name}, the normal fire season runs from month {start_m} ({MONTH_NAMES.get(start_m)}) "
                f"to month {end_m} ({MONTH_NAMES.get(end_m)}), peaking in month {peak_m} ({MONTH_NAMES.get(peak_m)}). "
                f"This season represents {share_pct}% of annual burning. (Data version: {dataset.data_version})."
            )

        else:
            # Default: yearly stats
            res_y, cit_y, log_y = dispatch_tool(
                "get_yearly_stats", {"area_id": target_area, "year": target_year}, dataset, cursor
            )
            tool_results.append(res_y)
            citations.append(cit_y)
            tool_logs.append(log_y)

            stats_list = res_y.get("stats", [])
            if stats_list:
                s = stats_list[0]
                tot = s["harmonized_total"]
                rank = s["rank"]
                vs_mean = s["vs_mean_pct"]
                answer = (
                    f"In {canonical_name}, {target_year} recorded {tot} harmonized fire events "
                    f"(historical rank: {rank}, {vs_mean}% vs mean). (Data version: {dataset.data_version})."
                )
            else:
                answer = f"No yearly records found for {canonical_name} in {target_year}."

        assert verify_grounding(answer, tool_results, extra_allowed={str(y) for y in found_years}), (
            "Replay answer failed grounding check"
        )

        return AskResponse(
            answer=answer,
            citations=citations,
            toolCalls=tool_logs,
            mode="replay",
        )
