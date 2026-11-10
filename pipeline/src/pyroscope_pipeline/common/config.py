"""Typed configuration loader using Pydantic."""

from pathlib import Path

import yaml
from pydantic import BaseModel


class DataPathsConfig(BaseModel):
    root_dir: str
    raw_dir: str
    interim_dir: str
    processed_dir: str
    reference_dir: str
    fixtures_dir: str


class ModisConfig(BaseModel):
    product: str
    collection: str
    min_confidence: int
    require_type_zero: bool


class ViirsConfig(BaseModel):
    product: str
    allowed_confidence: list[str]


class SourcesConfig(BaseModel):
    modis: ModisConfig
    viirs: ViirsConfig


class ClusteringConfig(BaseModel):
    algorithm: str
    eps_spatial_meters: float
    eps_temporal_hours: float
    min_pts: int


class SpatialConfig(BaseModel):
    bbox_bangladesh: list[float]
    h3_resolutions: list[int]


class HarmonizationConfig(BaseModel):
    min_mean_monthly_modis: int
    month_pool_width: int
    cv_method: str
    methods: list[str]
    percentiles: list[int]
    season_share_threshold: float


class PipelineConfig(BaseModel):
    data: DataPathsConfig
    sources: SourcesConfig
    clustering: ClusteringConfig
    spatial: SpatialConfig
    harmonization: HarmonizationConfig


def load_config(config_path: Path | str | None = None) -> PipelineConfig:
    """Load and validate pipeline configuration from YAML file."""
    if config_path is None:
        from pyroscope_pipeline.common.paths import PIPELINE_ROOT

        config_path = PIPELINE_ROOT / "config.yaml"

    path = Path(config_path)
    if not path.is_file():
        raise FileNotFoundError(f"Configuration file not found at: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        raise TypeError(f"Invalid configuration content in: {path}")

    return PipelineConfig.model_validate(data)
