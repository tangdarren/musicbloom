"""Favorite track repository."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from musicbloom.db.models.favorite_track import FavoriteTrack


class FavoriteTrackRepository:
    """Database access for favorited tracks."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def get_for_user_and_track(
        self,
        *,
        user_id: int,
        track_id: str,
    ) -> FavoriteTrack | None:
        """Return a favorite by user and track identifier."""
        return self._db.scalar(
            select(FavoriteTrack).where(
                FavoriteTrack.user_id == user_id,
                FavoriteTrack.track_id == track_id,
            ),
        )

    def list_for_user(self, user_id: int) -> list[FavoriteTrack]:
        """Return favorites for a user ordered newest first."""
        return list(
            self._db.scalars(
                select(FavoriteTrack)
                .where(FavoriteTrack.user_id == user_id)
                .order_by(FavoriteTrack.created_at.desc(), FavoriteTrack.id.desc()),
            ),
        )

    def add(self, *, user_id: int, track_id: str) -> FavoriteTrack:
        """Create a favorite when missing; return existing otherwise."""
        existing = self.get_for_user_and_track(user_id=user_id, track_id=track_id)
        if existing is not None:
            return existing

        favorite = FavoriteTrack(user_id=user_id, track_id=track_id)
        self._db.add(favorite)
        self._db.flush()
        self._db.refresh(favorite)
        return favorite

    def remove(self, *, user_id: int, track_id: str) -> bool:
        """Remove a favorite. Returns True when a row was deleted."""
        existing = self.get_for_user_and_track(user_id=user_id, track_id=track_id)
        if existing is None:
            return False
        self._db.delete(existing)
        self._db.flush()
        return True
