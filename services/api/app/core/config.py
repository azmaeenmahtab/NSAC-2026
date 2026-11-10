"""API Settings loaded via pydantic-settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    data_dir: str = "../../data/processed/current"
    web_origin: str = "http://localhost:3000"
    llm_provider: str = "replay"
    llm_model: str = "gemini-1.5-flash"
    gemini_api_key: str = ""
    app_db_path: str = "./app.db"


settings = Settings()
