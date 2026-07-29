"""Version 1 player API schemas."""

from pydantic import BaseModel, Field

from musicbloom.models.player import PlayerSession, RepeatMode


class PlayRequest(BaseModel):
    """Optional track selection for play requests."""

    track_id: str | None = Field(
        default=None,
        description="Catalog track to play immediately",
    )


class SeekRequest(BaseModel):
    """Seek request payload."""

    position_ms: int = Field(
        ge=0,
        description="Target playback position in milliseconds",
    )


class VolumeRequest(BaseModel):
    """Volume update payload."""

    level: float = Field(ge=0.0, le=1.0, description="Volume level from 0.0 to 1.0")


class ShuffleRequest(BaseModel):
    """Shuffle mode update payload."""

    enabled: bool = Field(description="Whether shuffle mode is enabled")


class RepeatRequest(BaseModel):
    """Repeat mode update payload."""

    mode: RepeatMode = Field(description="Repeat mode for queue playback")


class QueueTrackRequest(BaseModel):
    """Queue insertion payload."""

    track_id: str = Field(description="Catalog track to append to the queue")
    allow_duplicate: bool = Field(
        default=False,
        description="Allow duplicate entries for the same track",
    )


PlayerSessionResponse = PlayerSession

__all__ = [
    "PlayRequest",
    "PlayerSessionResponse",
    "QueueTrackRequest",
    "RepeatRequest",
    "SeekRequest",
    "ShuffleRequest",
    "VolumeRequest",
]
