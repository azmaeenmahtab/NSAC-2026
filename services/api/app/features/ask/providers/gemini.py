"""Live Gemini provider using google-genai Interactions API with tool calling."""

from __future__ import annotations

import json
import logging
from typing import Any

import duckdb
from google import genai
from google.genai import types

from app.core.config import settings
from app.core.dataset import LoadedDataset
from app.features.ask.grounding import build_deterministic_fallback_answer, verify_grounding
from app.features.ask.prompt import SYSTEM_PROMPT
from app.features.ask.providers.base import BaseLLMProvider
from app.features.ask.providers.replay import ReplayProvider
from app.features.ask.schemas import AskResponse, Citation, ToolCallLog
from app.features.ask.tools.registry import TOOL_SCHEMAS, dispatch_tool

logger = logging.getLogger("pyroscope.api.ask.gemini")


class GeminiProvider(BaseLLMProvider):
    """Interactions-API based Gemini provider supporting grounded function calling."""

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self.api_key = api_key or settings.gemini_api_key
        self.model = model or settings.llm_model
        self._fallback_replay = ReplayProvider()

    async def ask(
        self,
        question: str,
        area_id: str | None,
        style: str,
        dataset: LoadedDataset,
        cursor: duckdb.DuckDBPyConnection,
    ) -> AskResponse:
        """Execute multi-turn tool calling loop via Google Gemini Interactions API."""
        if not self.api_key:
            logger.info("No GEMINI_API_KEY provided; falling back to deterministic replay mode.")
            return await self._fallback_replay.ask(question, area_id, style, dataset, cursor)

        try:
            client = genai.Client(
                api_key=self.api_key,
                http_options=types.HttpOptions(timeout=20_000),  # 20s timeout in ms
            )

            user_query = f"{question} (Context area_id: {area_id})" if area_id else question

            interaction = client.interactions.create(
                model=self.model,
                system_instruction=SYSTEM_PROMPT,
                input=user_query,
                tools=TOOL_SCHEMAS,
            )

            tool_results: list[dict[str, Any]] = []
            citations: list[Citation] = []
            tool_logs: list[ToolCallLog] = []
            max_turns = 4
            turn = 0

            current_interaction = interaction

            while turn < max_turns:
                turn += 1
                function_calls: list[Any] = []
                for step in getattr(current_interaction, "steps", []):
                    if getattr(step, "type", None) == "function_call":
                        function_calls.append(step)

                if not function_calls:
                    break

                function_outputs: list[dict[str, Any]] = []
                for fc in function_calls:
                    call_name = getattr(fc, "name", "")
                    call_args = getattr(fc, "arguments", {}) or {}

                    try:
                        res, cit, log = dispatch_tool(call_name, call_args, dataset, cursor)
                        tool_results.append({"tool": call_name, "result": res})
                        citations.append(cit)
                        tool_logs.append(log)

                        function_outputs.append({
                            "type": "function_result",
                            "name": call_name,
                            "call_id": getattr(fc, "id", call_name),
                            "result": [{"type": "text", "text": json.dumps(res)}],
                        })
                    except Exception as err:  # noqa: BLE001
                        logger.warning("Tool execution error in %s: %s", call_name, err)
                        function_outputs.append({
                            "type": "function_result",
                            "name": call_name,
                            "call_id": getattr(fc, "id", call_name),
                            "result": [{"type": "text", "text": json.dumps({"error": str(err)})}],
                        })

                interaction_id = getattr(current_interaction, "id", None)
                current_interaction = client.interactions.create(
                    model=self.model,
                    system_instruction=SYSTEM_PROMPT,
                    input=function_outputs,
                    tools=TOOL_SCHEMAS,
                    previous_interaction_id=interaction_id,
                )

            answer = getattr(current_interaction, "output_text", "")
            if not answer:
                answer = build_deterministic_fallback_answer(tool_results, dataset.data_version)

            # Grounding check: verify that all numbers >= 10 in answer appear in tool results
            is_grounded = verify_grounding(answer, tool_results)
            if not is_grounded:
                logger.warning("LLM emitted ungrounded numbers; substituting deterministic answer")
                answer = build_deterministic_fallback_answer(tool_results, dataset.data_version)

            return AskResponse(
                answer=answer,
                citations=citations,
                toolCalls=tool_logs,
                mode="live",
            )

        except Exception as ex:  # noqa: BLE001
            logger.error("Gemini API interaction failed: %s; invoking replay fallback", ex)
            return await self._fallback_replay.ask(question, area_id, style, dataset, cursor)
