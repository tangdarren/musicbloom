"""Spotify player control request schemas."""

from pydantic import BaseModel, Field


class SpotifySeekRequest(BaseModel):
    """Request body for seeking within the active Spotify track."""

    position_ms: int = Field(
        ge=0,
        description="Target playback position in milliseconds",
    )


class SpotifyVolumeRequest(BaseModel):
    """Request body for setting Spotify playback volume."""

    level: float = Field(
        ge=0.0,
        le=1.0,
        description="Normalized volume level from 0.0 to 1.0",
    )
