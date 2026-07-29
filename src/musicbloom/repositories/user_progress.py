"""User progress repository."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from musicbloom.db.models.user_progress import UserProgress


class UserProgressRepository:
    """Database access for user progress."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def get_for_user(self, user_id: int) -> UserProgress | None:
        """Return progress for a user."""
        return self._db.scalar(
            select(UserProgress).where(UserProgress.user_id == user_id),
        )

    def add(self, progress: UserProgress) -> UserProgress:
        """Persist user progress."""
        self._db.add(progress)
        self._db.flush()
        self._db.refresh(progress)
        return progress

    def require_for_user(self, user_id: int) -> UserProgress:
        """Return progress for a user, raising if missing."""
        progress = self.get_for_user(user_id)
        if progress is None:
            msg = "User progress has not been initialized"
            raise RuntimeError(msg)
        return progress
