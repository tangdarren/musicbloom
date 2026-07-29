"""Domain models for Spotify playback metadata."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class SpotifyPlaybackStatus(StrEnum):
    """Normalized Spotify playback transport state."""

    IDLE = "idle"
    PLAYING = "playing"
    PAUSED = "paused"


class SpotifyPlayerDevice(BaseModel):
    """Active or available Spotify playback device."""

    id: str | None = Field(default=None, description="Spotify device identifier")
    name: str = Field(description="Human-readable device name")
    type: str = Field(description="Spotify device type")
    is_active: bool = Field(description="Whether this device is the active player")
    volume_percent: int | None = Field(
        default=None,
        ge=0,
        le=100,
        description="Device volume percentage when available",
    )


class SpotifyPlayerTrack(BaseModel):
    """Normalized Spotify track metadata exposed to clients."""

    track_id: str = Field(description="Spotify track identifier")
    title: str = Field(description="Track title")
    artist_name: str = Field(description="Primary artist display name")
    album_title: str | None = Field(default=None, description="Album title")
    duration_ms: int = Field(ge=0, description="Track duration in milliseconds")
    artwork_url: str | None = Field(
        default=None,
        description="Remote album artwork URL for display only",
    )
    spotify_uri: str | None = Field(
        default=None,
        description="Spotify URI for the track",
    )


class SpotifyRecentTrack(BaseModel):
    """Recently played Spotify track entry."""

    track: SpotifyPlayerTrack
    played_at: datetime = Field(description="UTC timestamp when the track was played")


class SpotifyPlayerSnapshot(BaseModel):
    """Public Spotify player state without token material."""

    status: SpotifyPlaybackStatus = Field(description="Normalized playback status")
    configured: bool = Field(
        description="Whether Spotify OAuth is configured on the server",
    )
    connected: bool = Field(description="Whether a Spotify account is connected")
    is_playing: bool = Field(description="Whether Spotify reports active playback")
    progress_ms: int | None = Field(
        default=None,
        ge=0,
        description="Current playback position in milliseconds",
    )
    track: SpotifyPlayerTrack | None = Field(
        default=None,
        description="Currently loaded track metadata",
    )
    device: SpotifyPlayerDevice | None = Field(
        default=None,
        description="Active playback device when available",
    )
    shuffle: bool | None = Field(default=None, description="Shuffle state when known")
    repeat_mode: str | None = Field(
        default=None,
        description="Spotify repeat mode when known",
    )
    recently_played: list[SpotifyRecentTrack] = Field(
        default_factory=list,
        description="Recent playback entries when available",
    )
    message: str | None = Field(
        default=None,
        description="Informational message for idle or unavailable states",
    )
    control_available: bool = Field(
        description="Whether playback controls can be sent to Spotify",
    )
    control_unavailable_reason: str | None = Field(
        default=None,
        description="Why playback controls are unavailable",
    )
