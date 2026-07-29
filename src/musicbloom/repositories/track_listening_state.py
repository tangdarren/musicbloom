"""Track listening state repository."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from musicbloom.db.models.track_listening_state import TrackListeningState


class TrackListeningStateRepository:
    """Database access for per-track listening progress."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def get_for_user_and_track(
        self,
        user_id: int,
        track_id: str,
    ) -> TrackListeningState | None:
        """Return listening state for a user and track."""
        return self._db.scalar(
            select(TrackListeningState).where(
                TrackListeningState.user_id == user_id,
                TrackListeningState.track_id == track_id,
            ),
        )

    def get_or_create(self, *, user_id: int, track_id: str) -> TrackListeningState:
        """Return existing track state or create a new record."""
        existing = self.get_for_user_and_track(user_id, track_id)
        if existing is not None:
            return existing

        state = TrackListeningState(
            user_id=user_id,
            track_id=track_id,
            validated_listening_ms=0,
            progress_points_awarded=0,
            progress_experience_awarded=0,
            completion_awarded=False,
            skipped=False,
            last_position_ms=0,
        )
        self._db.add(state)
        self._db.flush()
        self._db.refresh(state)
        return state

    def count_completed_for_user(self, user_id: int) -> int:
        """Return the number of tracks completed by a user."""
        return len(
            list(
                self._db.scalars(
                    select(TrackListeningState.track_id).where(
                        TrackListeningState.user_id == user_id,
                        TrackListeningState.completion_awarded.is_(True),
                    ),
                ),
            ),
        )
