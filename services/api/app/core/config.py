"""API Settings loaded via pydantic-settings."""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_REPO_ROOT = Path(__file__).resolve().parents[4]
_DEFAULT_FIXTURES_DIR = _REPO_ROOT / "data" / "fixtures"
_DEFAULT_REFERENCE_DIR = _REPO_ROOT / "data" / "reference"


class Settings(BaseSettings):
    """Environment-backed runtime settings for PyroScope API."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    data_dir: str = str(_DEFAULT_FIXTURES_DIR)
    reference_dir: str = str(_DEFAULT_REFERENCE_DIR)
    web_origin: str = "http://localhost:3000"
    llm_provider: str = "replay"
    llm_model: str = "gemini-3.8-flash"
    gemini_api_key: str = ""
    app_db_path: str = "./app.db"
    rate_limit_default: str = "120/minute"


settings = Settings()
