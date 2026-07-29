"""Database-backed player session repository."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from musicbloom.db.init import get_demo_user
from musicbloom.db.mappers.player_session import (
    apply_player_session_to_record,
    create_default_player_session_record,
    record_to_player_session,
)
from musicbloom.db.models.player_session import PlayerSessionRecord
from musicbloom.models.player import PlayerSession


class DatabasePlayerSessionRepository:
    """Persist player sessions in the database for the active demo user."""

    def __init__(self, db: Session, user_id: int) -> None:
        self._db = db
        self._user_id = user_id

    @classmethod
    def for_demo_user(cls, db: Session) -> "DatabasePlayerSessionRepository":
        """Create a repository scoped to the seeded demo user."""
        user = get_demo_user(db)
        return cls(db, user.id)

    def get_session(self) -> PlayerSession:
        """Return the current player session."""
        record = self._get_or_create_record()
        return record_to_player_session(record)

    def save_session(self, session: PlayerSession) -> PlayerSession:
        """Persist and return the updated player session."""
        record = self._get_or_create_record()
        apply_player_session_to_record(record, session)
        self._db.flush()
        self._db.refresh(record)
        return record_to_player_session(record)

    def _get_or_create_record(self) -> PlayerSessionRecord:
        record = self._db.scalar(
            select(PlayerSessionRecord).where(
                PlayerSessionRecord.user_id == self._user_id,
            ),
        )
        if record is None:
            record = create_default_player_session_record(self._user_id)
            self._db.add(record)
            self._db.flush()
            self._db.refresh(record)
        return record
