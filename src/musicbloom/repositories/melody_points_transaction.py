"""Melody points transaction repository."""

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from musicbloom.db.models.melody_points_transaction import MelodyPointsTransaction


class MelodyPointsTransactionRepository:
    """Database access for melody points transactions."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def add_transaction(
        self,
        *,
        user_id: int,
        amount: int,
        experience_amount: int,
        reason: str,
        explanation: str,
        track_id: str | None = None,
        listening_event_id: int | None = None,
        created_at: datetime | None = None,
    ) -> MelodyPointsTransaction:
        """Persist a melody points transaction."""
        transaction = MelodyPointsTransaction(
            user_id=user_id,
            amount=amount,
            experience_amount=experience_amount,
            reason=reason,
            explanation=explanation,
            track_id=track_id,
            listening_event_id=listening_event_id,
            created_at=created_at or datetime.now(tz=UTC),
        )
        self._db.add(transaction)
        self._db.flush()
        self._db.refresh(transaction)
        return transaction

    def list_for_event(self, listening_event_id: int) -> list[MelodyPointsTransaction]:
        """Return transactions linked to a listening event."""
        return list(
            self._db.scalars(
                select(MelodyPointsTransaction)
                .where(
                    MelodyPointsTransaction.listening_event_id == listening_event_id,
                )
                .order_by(MelodyPointsTransaction.created_at.asc()),
            ),
        )

    def count_for_user(self, user_id: int) -> int:
        """Return the number of transactions for a user."""
        return int(
            self._db.scalar(
                select(func.count())
                .select_from(MelodyPointsTransaction)
                .where(MelodyPointsTransaction.user_id == user_id),
            )
            or 0,
        )
