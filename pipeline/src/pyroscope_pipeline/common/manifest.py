"""Manifest reader and writer per DB_SCHEMA.md specifications."""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class SourceManifest(BaseModel):
    file_name: str
    sensor: str
    row_count: int
    sha256: str
    date_range: list[str]


class PipelineCounts(BaseModel):
    detections_raw: int = 0
    detections_kept: int = 0
    detections_dropped_confidence: int = 0
    detections_dropped_duplicate: int = 0
    events_created: int = 0
    noise_points: int = 0
    events_outside_roi: int = 0


class DatasetManifest(BaseModel):
    data_version: str
    pipeline_version: str = "0.1.0"
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    git_commit: str = "unknown"
    as_of_date: str
    provisional_from: str | None = None
    provisional_note: str | None = None
    parameters: dict[str, Any]
    sources: list[SourceManifest] = Field(default_factory=list)
    counts: PipelineCounts = Field(default_factory=PipelineCounts)
    unallocated_harmonized: float = 0.0

    def write_json(self, target_path: Path | str) -> None:
        """Write manifest to disk as formatted JSON."""
        path = Path(target_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.model_dump_json(indent=2))

    @classmethod
    def read_json(cls, source_path: Path | str) -> "DatasetManifest":
        """Read manifest from JSON file."""
        path = Path(source_path)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.model_validate(data)
