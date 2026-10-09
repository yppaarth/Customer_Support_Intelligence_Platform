from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    environment: str = "development"
    database_url: str = "sqlite:///./resolveiq.sqlite3"
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret: str = Field(default="dev-only-secret")
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    demo_login_enabled: bool = True
    ai_provider: str = "mock"
    openai_api_key: str | None = None
    classification_model: str = "gpt-4.1-mini"
    generation_model: str = "gpt-4.1"
    embedding_model: str = "text-embedding-3-small"
    frontend_origin: str = "http://localhost:5173"
    allowed_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    min_draft_confidence: float = 0.72
    min_retrieval_score: float = 0.24
    max_upload_bytes: int = 8_000_000

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
