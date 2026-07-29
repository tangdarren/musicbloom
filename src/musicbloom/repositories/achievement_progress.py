"""Achievement progress repository."""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from musicbloom.db.models.achievement_progress import AchievementProgress


class AchievementProgressRepository:
    """Database access for achievement progress."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def get_for_user_and_achievement(
        self,
        user_id: int,
        achievement_id: str,
    ) -> AchievementProgress | None:
        """Return achievement progress for a user."""
        return self._db.scalar(
            select(AchievementProgress).where(
                AchievementProgress.user_id == user_id,
                AchievementProgress.achievement_id == achievement_id,
            ),
        )

    def list_for_user(self, user_id: int) -> list[AchievementProgress]:
        """Return all achievement progress records for a user."""
        return list(
            self._db.scalars(
                select(AchievementProgress).where(
                    AchievementProgress.user_id == user_id,
                ),
            ),
        )

    def ensure_progress(
        self,
        *,
        user_id: int,
        achievement_id: str,
    ) -> AchievementProgress:
        """Return achievement progress, creating it when missing."""
        record = self.get_for_user_and_achievement(user_id, achievement_id)
        if record is not None:
            return record

        record = AchievementProgress(
            user_id=user_id,
            achievement_id=achievement_id,
            progress=0,
        )
        self._db.add(record)
        self._db.flush()
        self._db.refresh(record)
        return record

    def save_progress(
        self,
        *,
        record: AchievementProgress,
        progress: int,
        completed: bool,
    ) -> AchievementProgress:
        """Persist updated achievement progress."""
        record.progress = progress
        if completed and record.completed_at is None:
            record.completed_at = datetime.now(tz=UTC)
        self._db.flush()
        self._db.refresh(record)
        return record

    def mark_claimed(self, record: AchievementProgress) -> AchievementProgress:
        """Mark an achievement reward as claimed."""
        record.claimed_at = datetime.now(tz=UTC)
        self._db.flush()
        self._db.refresh(record)
        return record
