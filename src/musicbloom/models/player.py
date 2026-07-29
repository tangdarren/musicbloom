"""Player session domain models."""

from enum import StrEnum

from pydantic import BaseModel, Field, model_validator

from musicbloom.models.catalog import AccentTheme, AudioSource, TrackArtwork, TrackMood


class PlaybackState(StrEnum):
    """Current transport state for the player session."""

    PLAYING = "playing"
    PAUSED = "paused"
    STOPPED = "stopped"


class RepeatMode(StrEnum):
    """Queue repeat behavior."""

    OFF = "off"
    ONE = "one"
    ALL = "all"


class Volume(BaseModel):
    """Normalized output volume for the player session."""

    level: float = Field(ge=0.0, le=1.0, description="Volume level from 0.0 to 1.0")


class PlaybackPosition(BaseModel):
    """Validated playback position within a track."""

    position_ms: int = Field(ge=0, description="Playback position in milliseconds")

    def clamp_to_duration(self, duration_ms: int) -> "PlaybackPosition":
        """Return a copy clamped to the supplied track duration."""
        if duration_ms < 0:
            msg = "duration_ms must be non-negative"
            raise ValueError(msg)
        return PlaybackPosition(position_ms=min(self.position_ms, duration_ms))


class QueueItem(BaseModel):
    """Track entry waiting in the player queue."""

    track_id: str = Field(description="Stable catalog track identifier")
    title: str = Field(description="Track title")
    artist_name: str = Field(description="Artist display name")
    duration_ms: int = Field(ge=1, description="Track duration in milliseconds")


class ActiveTrack(BaseModel):
    """Currently loaded track with live playback metadata."""

    track_id: str = Field(description="Stable catalog track identifier")
    title: str = Field(description="Track title")
    artist_name: str = Field(description="Artist display name")
    album_title: str = Field(description="Album title")
    duration_ms: int = Field(ge=1, description="Track duration in milliseconds")
    artwork: TrackArtwork = Field(description="Track artwork reference")
    audio: AudioSource = Field(description="Client-side audio source reference")
    mood: TrackMood = Field(description="Track mood label")
    genre: str = Field(description="Primary genre label")
    accent_theme: AccentTheme = Field(description="Visual accent theme values")
    playable_in_demo_mode: bool = Field(
        description="Whether the track can be played in demo mode",
    )
    position: PlaybackPosition = Field(description="Current playback position")


class PlayerSession(BaseModel):
    """Full player session state returned by the API."""

    state: PlaybackState = Field(description="Current transport state")
    active_track: ActiveTrack | None = Field(
        default=None,
        description="Currently loaded track, if any",
    )
    queue: list[QueueItem] = Field(description="Ordered playback queue")
    queue_index: int | None = Field(
        default=None,
        description="Index of the active track within the queue, if aligned",
    )
    volume: Volume = Field(description="Current session volume")
    shuffle: bool = Field(description="Whether shuffle mode is enabled")
    repeat_mode: RepeatMode = Field(description="Current repeat mode")

    @model_validator(mode="after")
    def validate_queue_index(self) -> "PlayerSession":
        if self.queue_index is None:
            return self
        if self.queue_index < 0 or self.queue_index >= len(self.queue):
            msg = "queue_index must reference an item in the queue"
            raise ValueError(msg)
        return self


def create_initial_player_session() -> PlayerSession:
    """Build the default player session state."""
    return PlayerSession(
        state=PlaybackState.STOPPED,
        active_track=None,
        queue=[],
        queue_index=None,
        volume=Volume(level=0.8),
        shuffle=False,
        repeat_mode=RepeatMode.OFF,
    )
