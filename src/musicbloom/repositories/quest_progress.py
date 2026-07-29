"""Quest progress repository."""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from musicbloom.db.models.quest_progress import QuestProgress


class QuestProgressRepository:
    """Database access for quest progress."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def get_for_user_and_quest(
        self,
        user_id: int,
        quest_id: str,
    ) -> QuestProgress | None:
        """Return quest progress for a user."""
        return self._db.scalar(
            select(QuestProgress).where(
                QuestProgress.user_id == user_id,
                QuestProgress.quest_id == quest_id,
            ),
        )

    def list_for_user(self, user_id: int) -> list[QuestProgress]:
        """Return all quest progress records for a user."""
        return list(
            self._db.scalars(
                select(QuestProgress).where(QuestProgress.user_id == user_id),
            ),
        )

    def ensure_progress(
        self,
        *,
        user_id: int,
        quest_id: str,
        period_key: str,
    ) -> QuestProgress:
        """Return quest progress, creating or resetting it for the active period."""
        record = self.get_for_user_and_quest(user_id, quest_id)
        if record is None:
            record = QuestProgress(
                user_id=user_id,
                quest_id=quest_id,
                status="active",
                progress=0,
                period_key=period_key,
            )
            self._db.add(record)
            self._db.flush()
            self._db.refresh(record)
            return record

        if record.period_key != period_key:
            record.period_key = period_key
            record.status = "active"
            record.progress = 0
            record.completed_at = None
            record.claimed_at = None

        return record

    def save_progress(
        self,
        *,
        record: QuestProgress,
        status: str,
        progress: int,
        completed: bool,
    ) -> QuestProgress:
        """Persist updated quest progress."""
        record.status = status
        record.progress = progress
        if completed and record.completed_at is None:
            record.completed_at = datetime.now(tz=UTC)
        self._db.flush()
        self._db.refresh(record)
        return record

    def mark_claimed(self, record: QuestProgress) -> QuestProgress:
        """Mark a quest reward as claimed."""
        record.status = "claimed"
        record.claimed_at = datetime.now(tz=UTC)
        self._db.flush()
        self._db.refresh(record)
        return record
