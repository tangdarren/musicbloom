"""FastAPI dependency providers."""

from functools import lru_cache

from musicbloom.config import Settings


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()
