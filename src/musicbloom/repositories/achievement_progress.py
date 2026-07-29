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

    def upsert_progress(
        self,
        *,
        user_id: int,
        achievement_id: str,
        progress: int,
        completed: bool = False,
    ) -> AchievementProgress:
        """Create or update achievement progress."""
        record = self.get_for_user_and_achievement(user_id, achievement_id)
        if record is None:
            record = AchievementProgress(
                user_id=user_id,
                achievement_id=achievement_id,
                progress=progress,
                completed_at=datetime.now(tz=UTC) if completed else None,
            )
            self._db.add(record)
        else:
            record.progress = progress
            record.completed_at = datetime.now(tz=UTC) if completed else None
        self._db.flush()
        self._db.refresh(record)
        return record
