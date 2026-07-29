"""Listening event repository."""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from musicbloom.db.models.listening_event import ListeningEvent


class ListeningEventRepository:
    """Database access for listening events."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def add_event(
        self,
        *,
        user_id: int,
        track_id: str,
        event_type: str,
        position_ms: int = 0,
        occurred_at: datetime | None = None,
    ) -> ListeningEvent:
        """Persist a listening event."""
        event = ListeningEvent(
            user_id=user_id,
            track_id=track_id,
            event_type=event_type,
            position_ms=position_ms,
            occurred_at=occurred_at or datetime.now(tz=UTC),
        )
        self._db.add(event)
        self._db.flush()
        self._db.refresh(event)
        return event

    def list_for_user(self, user_id: int) -> list[ListeningEvent]:
        """Return listening events for a user ordered by occurrence time."""
        return list(
            self._db.scalars(
                select(ListeningEvent)
                .where(ListeningEvent.user_id == user_id)
                .order_by(ListeningEvent.occurred_at.desc()),
            ),
        )
