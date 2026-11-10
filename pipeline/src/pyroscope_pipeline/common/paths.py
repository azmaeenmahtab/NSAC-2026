"""Centralized filesystem paths for the pipeline."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
PIPELINE_ROOT = Path(__file__).resolve().parents[3]
DATA_ROOT = REPO_ROOT / "data"

RAW_DIR = DATA_ROOT / "raw"
INTERIM_DIR = DATA_ROOT / "interim"
PROCESSED_DIR = DATA_ROOT / "processed"
REFERENCE_DIR = DATA_ROOT / "reference"
FIXTURES_DIR = DATA_ROOT / "fixtures"
