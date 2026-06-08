# backend/app/core/config.py
from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    APP_NAME: str = "PM Weather API"
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    DATABASE_URL: str
    ALLOWED_ORIGINS: list[str] = Field(default_factory=list)

    OPENWEATHER_API_KEY: str = ""
    OPENWEATHER_BASE_URL: str = "https://api.openweathermap.org"
    OPENWEATHER_TIMEOUT_SECONDS: float = 10.0

    GROQ_API_KEY: str = ""
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"
    GROQ_INSIGHT_MODEL: str = "openai/gpt-oss-120b"
    GROQ_TIMEOUT_SECONDS: float = 20.0
    GROQ_MAX_COMPLETION_TOKENS: int = 512

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_origins(cls, value: object) -> list[str]:
        if isinstance(value, list):
            return [str(item).strip().strip('"').strip("'") for item in value if str(item).strip()]
        if isinstance(value, str):
            return [
                item.strip().strip('"').strip("'")
                for item in value.split(",")
                if item.strip().strip('"').strip("'")
            ]
        return []


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
