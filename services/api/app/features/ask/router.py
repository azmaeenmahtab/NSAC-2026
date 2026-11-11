"""HTTP route handler for `/api/ask` assistant endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Request

from app.core.dataset import LoadedDataset
from app.features.ask.schemas import AskEnvelope, AskRequest
from app.features.ask.service import AskService

router = APIRouter(tags=["ask"])
_default_service = AskService()


@router.post(
    "/api/ask",
    operation_id="askAssistant",
    response_model=AskEnvelope,
    summary="Ask PyroScope AI Assistant grounded in typed tool execution",
    description="Ask a fire-history question; answered only through typed tools with citations and replay mode.",
)
async def ask_endpoint(request: Request, body: AskRequest) -> AskEnvelope:
    """Handle assistant question submission."""
    dataset: LoadedDataset = request.app.state.dataset
    cursor = dataset.connection.cursor()
    try:
        return await _default_service.handle_ask(body, dataset, cursor)
    finally:
        cursor.close()

