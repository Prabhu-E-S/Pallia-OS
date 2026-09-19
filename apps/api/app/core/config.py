from functools import lru_cache
from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from the environment / `.env`."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Pallia OS API"
    app_version: str = "0.1.0"
    environment: str = "development"
    api_v1_prefix: str = "/api/v1"

    # PostgreSQL connection string.
    database_url: str = "postgresql+psycopg://pallia:pallia@localhost:5432/pallia"
    secret_key: str = "dev-secret-change-me"

    # Comma separated list of allowed CORS origins (development).
    cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:3000"]

    # Comma separated list of emails allowed to use the development login.
    # Empty means "any email" (development only).
    dev_login_allowed_emails: str = ""

    # Login rate limiting (in-memory; see app/core/rate_limit.py).
    login_max_attempts: int = 10
    login_rate_window_seconds: int = 900

    # Speech-to-text provider. "local" is a development-only service that reads
    # UTF-8 text from the uploaded payload; "openai" uses OpenAI Whisper.
    speech_provider: str = "local"

    # Structured-extraction provider. "local" is a deterministic, rule-based
    # extractor that works without network access; "openai" uses an LLM.
    ai_provider: str = "local"
    openai_api_key: str = ""
    openai_speech_model: str = "whisper-1"
    openai_extraction_model: str = "gpt-4o-mini"

    # Version of the extraction prompt; bumped whenever the schema/safety rules
    # change so stored extractions stay attributable.
    extraction_prompt_version: str = "v1"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_csv(cls, value) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        if isinstance(value, (list, tuple)):
            return list(value)
        return value

    @property
    def is_development(self) -> bool:
        return self.environment.lower() == "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()
