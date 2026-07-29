"""Application configuration loaded from environment variables."""

from typing import Annotated, Literal, Self

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

EnvironmentName = Literal["development", "staging", "production"]

DEFAULT_CORS_ORIGINS: list[str] = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]


def _parse_cors_origins(value: str | list[str]) -> list[str]:
    if isinstance(value, list):
        return value
    return [origin.strip() for origin in value.split(",") if origin.strip()]


class Settings(BaseSettings):
    """Typed application settings with environment-variable overrides."""

    model_config = SettingsConfigDict(
        env_prefix="MUSICBLOOM_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: EnvironmentName = "development"
    debug: bool = True
    api_host: str = "0.0.0.0"
    api_port: int = Field(default=8000, ge=1, le=65535)
    database_url: str | None = None
    demo_mode: bool = True
    cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: DEFAULT_CORS_ORIGINS.copy()
    )
    secret_key: SecretStr | None = None

    @property
    def resolved_database_url(self) -> str:
        """Return the configured database URL or the local SQLite default."""
        if self.database_url and self.database_url.strip():
            return self.database_url.strip()
        return "sqlite:///./musicbloom.db"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> list[str]:
        if value is None:
            return DEFAULT_CORS_ORIGINS.copy()
        if isinstance(value, str):
            return _parse_cors_origins(value)
        if isinstance(value, list):
            return [str(origin) for origin in value]
        msg = "cors_origins must be a comma-separated string or list"
        raise TypeError(msg)

    @model_validator(mode="after")
    def validate_production_configuration(self) -> Self:
        if self.environment != "production":
            return self

        errors: list[str] = []

        if self.secret_key is None or not self.secret_key.get_secret_value().strip():
            errors.append("secret_key is required in production")
        elif len(self.secret_key.get_secret_value()) < 32:
            errors.append("secret_key must be at least 32 characters in production")

        if self.demo_mode:
            errors.append("demo_mode must be disabled in production")

        if self.debug:
            errors.append("debug must be disabled in production")

        if not self.database_url or not self.database_url.strip():
            errors.append("database_url is required in production")

        if errors:
            raise ValueError("; ".join(errors))

        return self

    def __repr__(self) -> str:
        return (
            f"Settings(environment={self.environment!r}, debug={self.debug!r}, "
            f"api_host={self.api_host!r}, api_port={self.api_port!r}, "
            f"database_url={'set' if self.database_url else 'unset'}, "
            f"demo_mode={self.demo_mode!r}, cors_origins={self.cors_origins!r}, "
            f"secret_key={'**********' if self.secret_key else 'unset'})"
        )

    def __str__(self) -> str:
        return self.__repr__()
