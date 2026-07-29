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

    def upsert_progress(
        self,
        *,
        user_id: int,
        quest_id: str,
        status: str,
        progress: int,
        completed: bool = False,
    ) -> QuestProgress:
        """Create or update quest progress."""
        record = self.get_for_user_and_quest(user_id, quest_id)
        if record is None:
            record = QuestProgress(
                user_id=user_id,
                quest_id=quest_id,
                status=status,
                progress=progress,
                completed_at=datetime.now(tz=UTC) if completed else None,
            )
            self._db.add(record)
        else:
            record.status = status
            record.progress = progress
            record.completed_at = datetime.now(tz=UTC) if completed else None
        self._db.flush()
        self._db.refresh(record)
        return record
