"""User profile repository."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from musicbloom.db.models.user_profile import UserProfile


class UserProfileRepository:
    """Database access for user profiles."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_username(self, username: str) -> UserProfile | None:
        """Return a user profile by username."""
        return self._db.scalar(
            select(UserProfile).where(UserProfile.username == username),
        )

    def get_by_id(self, user_id: int) -> UserProfile | None:
        """Return a user profile by identifier."""
        return self._db.get(UserProfile, user_id)

    def add(self, user: UserProfile) -> UserProfile:
        """Persist a new user profile."""
        self._db.add(user)
        self._db.flush()
        self._db.refresh(user)
        return user
