"""Favorites business logic."""

from musicbloom.db.models.favorite_track import FavoriteTrack
from musicbloom.models.catalog import Track
from musicbloom.models.favorites import FavoritesResponse, FavoriteTrackItem
from musicbloom.repositories.favorite_track import FavoriteTrackRepository
from musicbloom.services.catalog import CatalogService
from musicbloom.services.favorites_errors import FavoriteTrackNotFoundError


class FavoritesService:
    """Manage persisted favorite tracks for the demo user."""

    def __init__(
        self,
        *,
        user_id: int,
        catalog_service: CatalogService,
        favorite_repository: FavoriteTrackRepository,
    ) -> None:
        self._user_id = user_id
        self._catalog_service = catalog_service
        self._favorites = favorite_repository

    def list_favorites(self) -> FavoritesResponse:
        """Return catalog-enriched favorites, newest first."""
        records = self._favorites.list_for_user(self._user_id)
        items: list[FavoriteTrackItem] = []
        for record in records:
            track = self._catalog_service.get_track(record.track_id)
            if track is None:
                continue
            items.append(self._to_item(record, track))
        return FavoritesResponse(items=items)

    def add_favorite(self, track_id: str) -> FavoriteTrackItem:
        """Favorite a track. Repeated requests return the existing favorite."""
        track = self._catalog_service.get_track(track_id)
        if track is None:
            raise FavoriteTrackNotFoundError(f"Track '{track_id}' was not found")

        record = self._favorites.add(user_id=self._user_id, track_id=track_id)
        return self._to_item(record, track)

    def remove_favorite(self, track_id: str) -> None:
        """Remove a favorite. Missing favorites are treated as success."""
        self._favorites.remove(user_id=self._user_id, track_id=track_id)

    @staticmethod
    def _to_item(record: FavoriteTrack, track: Track) -> FavoriteTrackItem:
        return FavoriteTrackItem(
            id=record.id,
            track_id=record.track_id,
            title=track.title,
            artist_name=track.artist_name,
            artwork=track.artwork,
            duration_ms=track.duration_ms,
            playable_in_demo_mode=track.playable_in_demo_mode,
            favorited_at=record.created_at,
        )
