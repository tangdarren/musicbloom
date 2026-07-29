"""Application configuration loaded from environment variables."""

from typing import Annotated, Literal, Self

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

EnvironmentName = Literal["development", "staging", "production"]

DEFAULT_SPOTIFY_SCOPES: list[str] = [
    "user-read-email",
    "user-read-private",
    "user-read-playback-state",
    "user-read-currently-playing",
    "user-modify-playback-state",
]

DEFAULT_SPOTIFY_SUCCESS_REDIRECT = "http://localhost:5173/?spotify=connected"
DEFAULT_SPOTIFY_FAILURE_REDIRECT = "http://localhost:5173/?spotify=error"

SPOTIFY_AUTHORIZE_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_PROFILE_URL = "https://api.spotify.com/v1/me"
SPOTIFY_API_BASE_URL = "https://api.spotify.com/v1"

OAUTH_STATE_COOKIE = "musicbloom_spotify_oauth_state"
OAUTH_STATE_MAX_AGE_SECONDS = 600

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
    token_encryption_key: SecretStr | None = None
    spotify_client_id: str | None = None
    spotify_client_secret: SecretStr | None = None
    spotify_redirect_uri: str | None = None
    spotify_scopes: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: DEFAULT_SPOTIFY_SCOPES.copy(),
    )
    spotify_frontend_success_redirect: str = DEFAULT_SPOTIFY_SUCCESS_REDIRECT
    spotify_frontend_failure_redirect: str = DEFAULT_SPOTIFY_FAILURE_REDIRECT

    @property
    def spotify_configured(self) -> bool:
        """Return True when Spotify OAuth credentials are fully configured."""
        return (
            self.spotify_client_id is not None
            and self.spotify_client_id.strip() != ""
            and self.spotify_client_secret is not None
            and self.spotify_client_secret.get_secret_value().strip() != ""
            and self.spotify_redirect_uri is not None
            and self.spotify_redirect_uri.strip() != ""
        )

    @property
    def resolved_token_encryption_key(self) -> SecretStr | None:
        """Return the configured token encryption key or fall back to secret_key."""
        if self.token_encryption_key is not None:
            return self.token_encryption_key
        return self.secret_key

    @property
    def resolved_oauth_state_secret(self) -> SecretStr | None:
        """Return the secret used to sign OAuth state cookies."""
        return self.secret_key or self.token_encryption_key

    @field_validator("spotify_scopes", mode="before")
    @classmethod
    def parse_spotify_scopes(cls, value: object) -> list[str]:
        if value is None:
            return DEFAULT_SPOTIFY_SCOPES.copy()
        if isinstance(value, str):
            return [scope.strip() for scope in value.split(",") if scope.strip()]
        if isinstance(value, list):
            return [str(scope) for scope in value]
        msg = "spotify_scopes must be a comma-separated string or list"
        raise TypeError(msg)

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
            f"secret_key={'**********' if self.secret_key else 'unset'}, "
            f"spotify_client_id={'set' if self.spotify_client_id else 'unset'}, "
            f"spotify_client_secret={self._repr_spotify_client_secret()})"
        )

    def _repr_spotify_client_secret(self) -> str:
        if self.spotify_client_secret:
            return "**********"
        return "unset"

    def __str__(self) -> str:
        return self.__repr__()
