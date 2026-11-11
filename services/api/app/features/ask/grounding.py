"""Grounding check: verify that all numerical assertions in model outputs originate from tools."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

logger = logging.getLogger("pyroscope.api.ask.grounding")


def extract_multidigit_numbers(text: str) -> list[str]:
    """Extract all integer numbers with 2 or more digits from text."""
    return re.findall(r"\b\d{2,}\b", text)


def verify_grounding(
    answer: str,
    tool_outputs: list[dict[str, Any]],
    extra_allowed: set[str] | None = None,
) -> bool:
    """Verify that every 2+ digit number in `answer` exists in tool outputs or allowed set.

    Args:
        answer: Generated natural language answer.
        tool_outputs: List of raw dict results returned by tools.
        extra_allowed: Additional numbers permitted (e.g. from user question).

    Returns:
        True if all multi-digit numbers are present in evidence, False otherwise.
    """
    numbers_in_answer = extract_multidigit_numbers(answer)
    if not numbers_in_answer:
        return True

    allowed_text = json.dumps(tool_outputs)
    allowed_set = extra_allowed or set()

    for num in numbers_in_answer:
        if num in allowed_set:
            continue
        # Check if the number appears as a token or substring in the serialized tool output
        if num not in allowed_text:
            logger.warning(
                "Ungrounded number '%s' detected in LLM answer not present in tool outputs",
                num,
            )
            return False

    return True


def build_deterministic_fallback_answer(
    tool_outputs: list[dict[str, Any]],
    data_version: str,
) -> str:
    """Build a deterministic grounded summary from tool outputs when LLM produces ungrounded numbers."""
    parts: list[str] = []

    for item in tool_outputs:
        tool_name = item.get("tool")
        result = item.get("result", {})

        if tool_name == "get_season":
            start_m = result.get("start_month")
            peak_m = result.get("peak_month")
            end_m = result.get("end_month")
            share = round(float(result.get("share_of_annual", 0.0)) * 100.0, 1)
            parts.append(
                f"Normal fire season spans months {start_m} to {end_m} (peak in month {peak_m}), "
                f"accounting for {share}% of annual burning."
            )

        elif tool_name == "get_anomalies":
            anomalies = result.get("anomalies", [])
            extreme_m = [str(a["month"]) for a in anomalies if a.get("class") == "extreme"]
            elevated_m = [str(a["month"]) for a in anomalies if a.get("class") == "elevated"]
            if extreme_m:
                parts.append(f"Recorded extreme burning in month(s): {', '.join(extreme_m)}.")
            elif elevated_m:
                parts.append(f"Recorded elevated burning in month(s): {', '.join(elevated_m)}.")
            else:
                parts.append("Activity for the evaluated year was normal.")

        elif tool_name == "get_yearly_stats":
            stats = result.get("stats", [])
            for s in stats:
                yr = s.get("year")
                total = s.get("harmonized_total")
                parts.append(f"Year {yr} recorded {total} harmonized fire events.")

    if not parts:
        parts.append("Data retrieved from tools.")

    parts.append(f"(Source: PyroScope {data_version}, strictly grounded).")
    return " ".join(parts)

