"""Listening event repository."""

from datetime import UTC, datetime

from sqlalchemy import func, select
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
        idempotency_key: str,
        position_ms: int = 0,
        occurred_at: datetime | None = None,
    ) -> ListeningEvent:
        """Persist a listening event."""
        event = ListeningEvent(
            user_id=user_id,
            track_id=track_id,
            event_type=event_type,
            idempotency_key=idempotency_key,
            position_ms=position_ms,
            occurred_at=occurred_at or datetime.now(tz=UTC),
        )
        self._db.add(event)
        self._db.flush()
        self._db.refresh(event)
        return event

    def get_by_idempotency_key(
        self,
        *,
        user_id: int,
        idempotency_key: str,
    ) -> ListeningEvent | None:
        """Return an event by user and idempotency key."""
        return self._db.scalar(
            select(ListeningEvent).where(
                ListeningEvent.user_id == user_id,
                ListeningEvent.idempotency_key == idempotency_key,
            ),
        )

    def list_for_user(self, user_id: int) -> list[ListeningEvent]:
        """Return listening events for a user ordered by occurrence time."""
        return list(
            self._db.scalars(
                select(ListeningEvent)
                .where(ListeningEvent.user_id == user_id)
                .order_by(ListeningEvent.occurred_at.desc()),
            ),
        )

    def list_recent_for_user(
        self,
        user_id: int,
        *,
        limit: int = 50,
        event_types: tuple[str, ...] = ("started", "completed", "skipped"),
    ) -> list[ListeningEvent]:
        """Return recent activity events for history, newest first."""
        return list(
            self._db.scalars(
                select(ListeningEvent)
                .where(
                    ListeningEvent.user_id == user_id,
                    ListeningEvent.event_type.in_(event_types),
                )
                .order_by(ListeningEvent.occurred_at.desc())
                .limit(limit),
            ),
        )

    def list_completed_track_ids_in_period(
        self,
        *,
        user_id: int,
        start: datetime,
        end: datetime,
    ) -> list[str]:
        """Return track IDs completed by a user within a UTC period."""
        return list(
            self._db.scalars(
                select(ListeningEvent.track_id)
                .where(
                    ListeningEvent.user_id == user_id,
                    ListeningEvent.event_type == "completed",
                    ListeningEvent.occurred_at >= start,
                    ListeningEvent.occurred_at <= end,
                )
                .distinct(),
            ),
        )

    def count_for_user(self, user_id: int) -> int:
        """Return the number of listening events for a user."""
        return int(
            self._db.scalar(
                select(func.count())
                .select_from(ListeningEvent)
                .where(ListeningEvent.user_id == user_id),
            )
            or 0,
        )
