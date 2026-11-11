"""Service layer orchestrating assistant tool execution, security, and audit logging."""

from __future__ import annotations

import logging

import duckdb

from app.core.config import settings
from app.core.dataset import LoadedDataset
from app.core.errors import ValidationAPIError
from app.core.responses import ResponseMeta
from app.features.ask.prompt import PROMPT_INJECTION_REFUSAL, check_prompt_injection
from app.features.ask.providers.base import BaseLLMProvider
from app.features.ask.providers.gemini import GeminiProvider
from app.features.ask.providers.replay import ReplayProvider
from app.features.ask.repository import log_ask_interaction
from app.features.ask.schemas import AskEnvelope, AskRequest, AskResponse

logger = logging.getLogger("pyroscope.api.ask")


def _get_provider(provider_type: str | None = None) -> BaseLLMProvider:
    ptype = (provider_type or settings.llm_provider).lower()
    if ptype == "gemini":
        return GeminiProvider()
    return ReplayProvider()


class AskService:
    """Core business service for Ask PyroScope operations."""

    def __init__(self, provider: BaseLLMProvider | None = None) -> None:
        self.provider = provider or _get_provider()

    async def handle_ask(
        self,
        request: AskRequest,
        dataset: LoadedDataset,
        cursor: duckdb.DuckDBPyConnection,
    ) -> AskEnvelope:
        """Process user question with input length validation, security checks, and logging."""
        cleaned_question = request.question.strip()
        if not cleaned_question:
            raise ValidationAPIError("question must not be empty")

        if len(cleaned_question) > 500:
            raise ValidationAPIError("question must not exceed 500 characters")

        # 1. Prompt Injection Defense
        if check_prompt_injection(cleaned_question):
            logger.info("Prompt injection detected in query; returning standard refusal")
            refusal_response = AskResponse(
                answer=PROMPT_INJECTION_REFUSAL,
                citations=[],
                toolCalls=[],
                mode="replay" if isinstance(self.provider, ReplayProvider) else "live",
            )
            # Log refusal to database
            log_ask_interaction(
                question=cleaned_question,
                mode=refusal_response.mode,
                tool_calls=[],
                answer=refusal_response.answer,
                data_version=dataset.data_version,
            )
            return AskEnvelope(
                data=refusal_response,
                meta=ResponseMeta(dataVersion=dataset.data_version, asOf=dataset.as_of),
            )

        # 2. Execute assistant workflow via active provider
        response = await self.provider.ask(
            question=cleaned_question,
            area_id=request.area_id,
            style=request.style,
            dataset=dataset,
            cursor=cursor,
        )

        # 3. Log interaction to SQLite ask_log audit table
        tool_call_dicts = [call.model_dump() for call in response.toolCalls]
        log_ask_interaction(
            question=cleaned_question,
            mode=response.mode,
            tool_calls=tool_call_dicts,
            answer=response.answer,
            data_version=dataset.data_version,
        )

        # 4. Construct standard API response envelope
        return AskEnvelope(
            data=response,
            meta=ResponseMeta(dataVersion=dataset.data_version, asOf=dataset.as_of),
        )
