"""Domain models for favorite tracks."""

from datetime import datetime

from pydantic import BaseModel, Field

from musicbloom.models.catalog import TrackArtwork


class FavoriteTrackItem(BaseModel):
    """A catalog-enriched favorite track entry."""

    id: int = Field(description="Favorite record identifier")
    track_id: str = Field(description="Catalog track identifier")
    title: str = Field(description="Track title")
    artist_name: str = Field(description="Track artist name")
    artwork: TrackArtwork = Field(description="Track artwork")
    duration_ms: int = Field(ge=0, description="Track duration in milliseconds")
    playable_in_demo_mode: bool = Field(
        description="Whether the track can be played in demo mode",
    )
    favorited_at: datetime = Field(
        description="UTC timestamp when the track was favorited",
    )


class FavoritesResponse(BaseModel):
    """Favorite tracks for the current demo user."""

    items: list[FavoriteTrackItem] = Field(
        default_factory=list,
        description="Favorite tracks ordered newest first",
    )
