from pathlib import Path

import pytest
from pydantic import ValidationError

from pyroscope_pipeline.common.config import PipelineConfig, load_config


def test_load_valid_config(tmp_path: Path) -> None:
    yaml_content = """
data:
  root_dir: "../data"
  raw_dir: "../data/raw"
  interim_dir: "../data/interim"
  processed_dir: "../data/processed"
  reference_dir: "../data/reference"
  fixtures_dir: "../data/fixtures"
sources:
  modis:
    product: "MCD14DL"
    collection: "C6.1"
    min_confidence: 30
    require_type_zero: true
  viirs:
    product: "VNP14IMGTDL"
    allowed_confidence: ["n", "h"]
clustering:
  algorithm: "st_dbscan"
  eps_spatial_meters: 2700.0
  eps_temporal_hours: 24.0
  min_pts: 2
spatial:
  bbox_bangladesh: [88.0, 20.5, 92.8, 26.7]
  h3_resolutions: [5, 6, 7]
harmonization:
  min_mean_monthly_modis: 3
  month_pool_width: 1
  cv_method: "leave_one_year_out"
  methods: ["quantile_map", "ratio"]
  percentiles: [50, 90, 95]
  season_share_threshold: 0.7
"""
    config_file = tmp_path / "config.yaml"
    config_file.write_text(yaml_content, encoding="utf-8")

    cfg = load_config(config_file)
    assert isinstance(cfg, PipelineConfig)
    assert cfg.clustering.eps_spatial_meters == 2700.0
    assert cfg.harmonization.min_mean_monthly_modis == 3


def test_missing_required_key_fails(tmp_path: Path) -> None:
    incomplete_yaml = """
data:
  root_dir: "../data"
"""
    config_file = tmp_path / "incomplete.yaml"
    config_file.write_text(incomplete_yaml, encoding="utf-8")

    with pytest.raises(ValidationError):
        load_config(config_file)


def test_non_dict_yaml_fails(tmp_path: Path) -> None:
    non_dict_yaml = "- item1\n- item2\n"
    config_file = tmp_path / "invalid.yaml"
    config_file.write_text(non_dict_yaml, encoding="utf-8")

    with pytest.raises(TypeError):
        load_config(config_file)


def test_load_repo_default_config() -> None:
    cfg = load_config()
    assert cfg.clustering.algorithm == "st_dbscan"
    assert cfg.spatial.h3_resolutions == [5, 6, 7]
