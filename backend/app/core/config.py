from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    DATABASE_URL: str = (
        "postgresql+asyncpg://postgres:password@localhost:5432/codevector"
    )
    TEST_DATABASE_URL: str = (
        "postgresql+asyncpg://postgres:password@localhost:5432/codevector_test"
    )

    @field_validator("DATABASE_URL", "TEST_DATABASE_URL", mode="before")
    @classmethod
    def normalize_db_url(cls, v: str) -> str:
        """Render's connectionString uses postgres:// or postgresql:// — asyncpg needs postgresql+asyncpg://."""
        if isinstance(v, str):
            if v.startswith("postgres://"):
                return "postgresql+asyncpg://" + v[len("postgres://"):]
            if v.startswith("postgresql://") and "+asyncpg" not in v:
                return "postgresql+asyncpg://" + v[len("postgresql://"):]
        return v

    # Application
    APP_NAME: str = "CodeVector Product API"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # Pagination
    MAX_PAGE_LIMIT: int = 100
    DEFAULT_PAGE_LIMIT: int = 20

    @field_validator("MAX_PAGE_LIMIT")
    @classmethod
    def max_limit_positive(cls, v: int) -> int:
        if v < 1:
            raise ValueError("MAX_PAGE_LIMIT must be >= 1")
        return v

    @field_validator("DEFAULT_PAGE_LIMIT")
    @classmethod
    def default_limit_positive(cls, v: int) -> int:
        if v < 1:
            raise ValueError("DEFAULT_PAGE_LIMIT must be >= 1")
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
