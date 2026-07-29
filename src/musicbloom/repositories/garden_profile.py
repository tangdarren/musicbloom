"""Garden profile repository."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from musicbloom.db.models.garden_profile import GardenProfile


class GardenProfileRepository:
    """Database access for garden profiles."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def get_for_user(self, user_id: int) -> GardenProfile | None:
        """Return the garden profile for a user."""
        return self._db.scalar(
            select(GardenProfile).where(GardenProfile.user_id == user_id),
        )

    def add(self, profile: GardenProfile) -> GardenProfile:
        """Persist a garden profile."""
        self._db.add(profile)
        self._db.flush()
        self._db.refresh(profile)
        return profile
