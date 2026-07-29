"""Decoration unlock repository."""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from musicbloom.db.models.decoration_unlock import DecorationUnlockRecord


class DecorationUnlockRepository:
    """Database access for unlocked decorations."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def get_for_user_and_decoration(
        self,
        user_id: int,
        decoration_id: str,
    ) -> DecorationUnlockRecord | None:
        """Return an unlock record for a user and decoration."""
        return self._db.scalar(
            select(DecorationUnlockRecord).where(
                DecorationUnlockRecord.user_id == user_id,
                DecorationUnlockRecord.decoration_id == decoration_id,
            ),
        )

    def unlock(
        self,
        *,
        user_id: int,
        decoration_id: str,
        unlocked_at: datetime | None = None,
    ) -> DecorationUnlockRecord:
        """Create or return an unlocked decoration record."""
        existing = self.get_for_user_and_decoration(user_id, decoration_id)
        if existing is not None:
            return existing

        record = DecorationUnlockRecord(
            user_id=user_id,
            decoration_id=decoration_id,
            unlocked_at=unlocked_at or datetime.now(tz=UTC),
        )
        self._db.add(record)
        self._db.flush()
        self._db.refresh(record)
        return record

    def list_for_user(self, user_id: int) -> list[DecorationUnlockRecord]:
        """Return unlocked decorations for a user."""
        return list(
            self._db.scalars(
                select(DecorationUnlockRecord)
                .where(DecorationUnlockRecord.user_id == user_id)
                .order_by(DecorationUnlockRecord.unlocked_at.desc()),
            ),
        )
