"""Repository for loading and filtering wildland guidance checklist items."""

from __future__ import annotations

import json
from pathlib import Path

from app.core.config import settings
from app.features.guidance.schemas import GuidanceItem, GuidanceStage

_CACHED_ITEMS: list[GuidanceItem] | None = None


def get_guidance_path() -> Path:
    """Return the absolute path to `guidance.json`."""
    return Path(settings.reference_dir) / "guidance.json"


def load_guidance_items(path: Path | None = None) -> list[GuidanceItem]:
    """Load and parse guidance items from reference JSON."""
    target_path = path or get_guidance_path()
    if not target_path.exists():
        return []

    content = target_path.read_text(encoding="utf-8")
    raw_list = json.loads(content)
    if not isinstance(raw_list, list):
        return []

    return [GuidanceItem.model_validate(item) for item in raw_list]


def get_all_guidance_items() -> list[GuidanceItem]:
    """Retrieve all guidance items with in-memory caching."""
    global _CACHED_ITEMS
    if _CACHED_ITEMS is None:
        _CACHED_ITEMS = load_guidance_items()
    return list(_CACHED_ITEMS)


def clear_guidance_cache() -> None:
    """Clear the cached guidance items."""
    global _CACHED_ITEMS
    _CACHED_ITEMS = None


def filter_guidance_items(
    items: list[GuidanceItem],
    stage: GuidanceStage | None = None,
    audience: str | None = None,
) -> list[GuidanceItem]:
    """Filter guidance items by stage and/or audience."""
    filtered = items
    if stage is not None:
        filtered = [item for item in filtered if item.stage == stage]
    if audience is not None:
        aud_clean = audience.strip().lower()
        if aud_clean and aud_clean != "all":
            filtered = [item for item in filtered if aud_clean in item.audience.lower()]
    return filtered

