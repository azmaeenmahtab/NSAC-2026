"""Pydantic schemas for `/api/ask` matching contracts/openapi.yaml."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.core.responses import ResponseMeta


class AskRequest(BaseModel):
    """User question request payload."""

    model_config = ConfigDict(extra="ignore")

    question: str = Field(..., max_length=500, description="User question in natural language (max 500 chars)")
    area_id: str | None = Field(default=None, description="Optional pre-selected area identifier or name")
    style: Literal["standard", "plain"] = Field(default="standard", description="Response wording style")


class Citation(BaseModel):
    """Data and tool citation supporting an answer."""

    model_config = ConfigDict(extra="ignore")

    tool: str = Field(..., description="Tool name that produced the cited data")
    areaId: str | None = Field(default=None, description="Resolved area identifier")
    years: list[int] = Field(default_factory=list, description="Years included in the evidence")
    dataVersion: str = Field(..., description="Dataset version cited")


class ToolCallLog(BaseModel):
    """Executed tool call audit log for UI timeline."""

    model_config = ConfigDict(extra="ignore")

    name: str = Field(..., description="Executed tool name")
    args: dict[str, Any] = Field(default_factory=dict, description="Tool invocation arguments")
    durationMs: float = Field(..., description="Tool execution wall-clock time in milliseconds")


class AskResponse(BaseModel):
    """Grounded assistant response."""

    model_config = ConfigDict(extra="ignore")

    answer: str = Field(..., description="Natural language response text strictly grounded in tools")
    citations: list[Citation] = Field(default_factory=list, description="Tools and data versions cited")
    toolCalls: list[ToolCallLog] = Field(default_factory=list, description="Timeline of tool calls")
    mode: Literal["live", "replay"] = Field(..., description="Execution mode: live LLM or offline replay")


class AskEnvelope(BaseModel):
    """Standard API response envelope for `/api/ask`."""

    data: AskResponse
    meta: ResponseMeta

