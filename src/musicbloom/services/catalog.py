"""Catalog business logic."""

import math

from musicbloom.models.catalog import (
    Album,
    Artist,
    PaginatedTrackResponse,
    Track,
    TrackMood,
)
from musicbloom.repositories.demo_catalog import DemoCatalogRepository


class CatalogService:
    """Service layer for querying the demo music catalog."""

    def __init__(self, repository: DemoCatalogRepository) -> None:
        self._repository = repository

    def list_artists(self) -> list[Artist]:
        """Return all demo artists."""
        return self._repository.list_artists()

    def list_albums(self) -> list[Album]:
        """Return all demo albums."""
        return self._repository.list_albums()

    def get_track(self, track_id: str) -> Track | None:
        """Return a single demo track by identifier."""
        return self._repository.get_track(track_id)

    def list_tracks(
        self,
        *,
        page: int,
        page_size: int,
        artist: str | None = None,
        album: str | None = None,
        genre: str | None = None,
        mood: TrackMood | None = None,
    ) -> PaginatedTrackResponse:
        """Return a filtered, paginated track collection."""
        filtered = self._filter_tracks(
            artist=artist,
            album=album,
            genre=genre,
            mood=mood,
        )
        total = len(filtered)
        total_pages = math.ceil(total / page_size) if total else 0
        start = (page - 1) * page_size
        end = start + page_size

        return PaginatedTrackResponse(
            items=filtered[start:end],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    def _filter_tracks(
        self,
        *,
        artist: str | None,
        album: str | None,
        genre: str | None,
        mood: TrackMood | None,
    ) -> list[Track]:
        tracks = self._repository.list_tracks()

        if artist is not None:
            needle = artist.casefold()
            tracks = [
                track
                for track in tracks
                if needle in track.artist_name.casefold()
                or needle in track.artist_id.casefold()
            ]

        if album is not None:
            needle = album.casefold()
            tracks = [
                track
                for track in tracks
                if needle in track.album_title.casefold()
                or needle in track.album_id.casefold()
            ]

        if genre is not None:
            needle = genre.casefold()
            tracks = [track for track in tracks if needle in track.genre.casefold()]

        if mood is not None:
            tracks = [track for track in tracks if track.mood == mood]

        return tracks
