"""FastAPI router for `/api/alerts` subscription and active alert endpoints."""

from __future__ import annotations

from typing import Annotated

import duckdb
from fastapi import APIRouter, Depends, Query

from app.core.config import Settings
from app.core.dataset import LoadedDataset
from app.core.db import get_app_settings, get_dataset, get_db_cursor
from app.core.errors import ValidationAPIError
from app.features.alerts.schemas import (
    ActiveAlertsEnvelope,
    ConfirmEnvelope,
    SubscriptionEnvelope,
    SubscriptionRequest,
    UnsubscribeEnvelope,
)
from app.features.alerts.service import (
    confirm,
    get_active_alerts,
    subscribe,
    unsubscribe,
)

router = APIRouter(prefix="/api/alerts", tags=["Alerts"])

DatasetDep = Annotated[LoadedDataset, Depends(get_dataset)]
CursorDep = Annotated[duckdb.DuckDBPyConnection, Depends(get_db_cursor)]
SettingsDep = Annotated[Settings, Depends(get_app_settings)]


@router.post(
    "/subscriptions",
    operation_id="subscribeAlerts",
    response_model=SubscriptionEnvelope,
)
async def post_subscription(
    dataset: DatasetDep,
    cursor: CursorDep,
    app_settings: SettingsDep,
    body: SubscriptionRequest,
) -> SubscriptionEnvelope:
    """Subscribe to fire season or elevated burning warnings."""
    data = subscribe(dataset=dataset, cursor=cursor, req=body, db_path=app_settings.app_db_path)
    return SubscriptionEnvelope(data=data)


@router.get(
    "/subscriptions/confirm",
    operation_id="confirmAlerts",
    response_model=ConfirmEnvelope,
)
async def get_confirm_subscription(
    token: Annotated[str, Query(description="Subscription confirmation token")],
    app_settings: SettingsDep,
) -> ConfirmEnvelope:
    """Confirm a pending alert subscription."""
    data = confirm(token=token, db_path=app_settings.app_db_path)
    return ConfirmEnvelope(data=data)


@router.delete(
    "/subscriptions",
    operation_id="unsubscribeAlerts",
    response_model=UnsubscribeEnvelope,
)
async def delete_subscription(
    token: Annotated[str, Query(description="Unique unsubscribe token")],
    app_settings: SettingsDep,
) -> UnsubscribeEnvelope:
    """Unsubscribe from alert notifications."""
    data = unsubscribe(token=token, db_path=app_settings.app_db_path)
    return UnsubscribeEnvelope(data=data)


@router.get(
    "/active",
    operation_id="getActiveAlerts",
    response_model=ActiveAlertsEnvelope,
)
async def get_active(
    dataset: DatasetDep,
    cursor: CursorDep,
    area_id: Annotated[
        str | None,
        Query(description="Region ID, preset ID, or bbox:<w>,<s>,<e>,<n>"),
    ] = None,
    area: Annotated[
        str | None,
        Query(description="Alias for area_id"),
    ] = None,
) -> ActiveAlertsEnvelope:
    """Active advisory alert status for an area."""
    target_area = area_id or area
    if not target_area:
        raise ValidationAPIError("Query parameter 'area_id' (or 'area') is required")
    return get_active_alerts(dataset=dataset, cursor=cursor, area_id=target_area)
