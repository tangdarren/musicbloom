"""Domain models for the demo music catalog."""

from enum import StrEnum

from pydantic import BaseModel, Field, model_validator


class TrackMood(StrEnum):
    """Mood classification for garden-themed demo tracks."""

    CALM = "calm"
    PLAYFUL = "playful"
    DREAMY = "dreamy"
    ENERGETIC = "energetic"
    COZY = "cozy"
    MYSTERIOUS = "mysterious"


class AudioSource(BaseModel):
    """Reference to playable audio content."""

    url: str | None = Field(default=None, description="Remote audio URL")
    local_path: str | None = Field(default=None, description="Local audio file path")

    @model_validator(mode="after")
    def validate_source_present(self) -> "AudioSource":
        if not self.url and not self.local_path:
            msg = "AudioSource requires either url or local_path"
            raise ValueError(msg)
        return self


class TrackArtwork(BaseModel):
    """Reference to track or album artwork."""

    url: str | None = Field(default=None, description="Remote artwork URL")
    local_path: str | None = Field(default=None, description="Local artwork file path")

    @model_validator(mode="after")
    def validate_artwork_present(self) -> "TrackArtwork":
        if not self.url and not self.local_path:
            msg = "TrackArtwork requires either url or local_path"
            raise ValueError(msg)
        return self


class AccentTheme(BaseModel):
    """Visual accent colors for player and garden theming."""

    primary: str = Field(description="Primary accent color (hex)")
    secondary: str = Field(description="Secondary accent color (hex)")
    background: str | None = Field(
        default=None,
        description="Optional background tint (hex)",
    )


class Artist(BaseModel):
    """Demo catalog artist."""

    id: str = Field(description="Stable artist identifier")
    name: str = Field(description="Display name")
    genre: str = Field(description="Primary genre label")


class Album(BaseModel):
    """Demo catalog album."""

    id: str = Field(description="Stable album identifier")
    title: str = Field(description="Album title")
    artist_id: str = Field(description="Associated artist identifier")
    artist_name: str = Field(description="Associated artist display name")
    artwork: TrackArtwork = Field(description="Album cover artwork")
    genre: str = Field(description="Primary genre label")


class Track(BaseModel):
    """Demo catalog track with playback metadata."""

    id: str = Field(description="Stable track identifier")
    title: str = Field(description="Track title")
    artist_id: str = Field(description="Associated artist identifier")
    artist_name: str = Field(description="Associated artist display name")
    album_id: str = Field(description="Associated album identifier")
    album_title: str = Field(description="Associated album title")
    duration_ms: int = Field(ge=1, description="Track duration in milliseconds")
    artwork: TrackArtwork = Field(description="Track artwork")
    audio: AudioSource = Field(description="Playable audio source")
    mood: TrackMood = Field(description="Track mood for garden reactions")
    genre: str = Field(description="Primary genre label")
    accent_theme: AccentTheme = Field(description="Visual accent theme values")
    playable_in_demo_mode: bool = Field(
        description="Whether the track can be played without Spotify credentials",
    )


class PaginatedTrackResponse(BaseModel):
    """Paginated collection of demo tracks."""

    items: list[Track] = Field(description="Tracks for the requested page")
    total: int = Field(ge=0, description="Total tracks matching the query")
    page: int = Field(ge=1, description="Current page number")
    page_size: int = Field(ge=1, description="Number of items per page")
    total_pages: int = Field(ge=0, description="Total pages available")
