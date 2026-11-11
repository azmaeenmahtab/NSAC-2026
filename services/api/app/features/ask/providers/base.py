"""Abstract LLM Provider interface for Ask PyroScope."""

from __future__ import annotations

from abc import ABC, abstractmethod

import duckdb

from app.core.dataset import LoadedDataset
from app.features.ask.schemas import AskResponse


class BaseLLMProvider(ABC):
    """Abstract interface defining assistant generation workflow."""

    @abstractmethod
    async def ask(
        self,
        question: str,
        area_id: str | None,
        style: str,
        dataset: LoadedDataset,
        cursor: duckdb.DuckDBPyConnection,
    ) -> AskResponse:
        """Process question and return grounded AskResponse."""
