"""Domain models for Spotify account connection."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class SpotifyConnectionStatusCode(StrEnum):
    """High-level Spotify connection states exposed to clients."""

    DISCONNECTED = "disconnected"
    CONNECTED = "connected"
    ERROR = "error"


class SpotifyConnectionStatus(BaseModel):
    """Public Spotify connection status without token material."""

    status: SpotifyConnectionStatusCode = Field(description="Connection state")
    configured: bool = Field(
        description="Whether Spotify OAuth is configured on the server",
    )
    display_name: str | None = Field(
        default=None,
        description="Connected Spotify display name",
    )
    spotify_user_id: str | None = Field(
        default=None,
        description="Connected Spotify user identifier",
    )
    scopes: list[str] = Field(
        default_factory=list,
        description="Granted OAuth scopes",
    )
    expires_at: datetime | None = Field(
        default=None,
        description="UTC access-token expiration timestamp",
    )
    error_code: str | None = Field(
        default=None,
        description="Machine-readable error code when status is error",
    )
    error_message: str | None = Field(
        default=None,
        description="Human-readable error message when status is error",
    )


class SpotifyDisconnectResult(BaseModel):
    """Result of disconnecting a Spotify account."""

    disconnected: bool = Field(description="Whether a connection was removed")
