"""Spotify OAuth connection repository."""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from musicbloom.db.models.spotify_connection import SpotifyConnectionRecord


class SpotifyConnectionRepository:
    """Database access for Spotify OAuth connections."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def get_for_user(self, user_id: int) -> SpotifyConnectionRecord | None:
        """Return the Spotify connection for a user."""
        return self._db.scalar(
            select(SpotifyConnectionRecord).where(
                SpotifyConnectionRecord.user_id == user_id,
            ),
        )

    def upsert_connection(
        self,
        *,
        user_id: int,
        spotify_user_id: str,
        display_name: str | None,
        encrypted_access_token: str,
        encrypted_refresh_token: str,
        token_expires_at: datetime,
        scopes: str,
    ) -> SpotifyConnectionRecord:
        """Create or replace a Spotify connection for a user."""
        record = self.get_for_user(user_id)
        if record is None:
            record = SpotifyConnectionRecord(
                user_id=user_id,
                spotify_user_id=spotify_user_id,
                display_name=display_name,
                encrypted_access_token=encrypted_access_token,
                encrypted_refresh_token=encrypted_refresh_token,
                token_expires_at=token_expires_at,
                scopes=scopes,
            )
            self._db.add(record)
        else:
            record.spotify_user_id = spotify_user_id
            record.display_name = display_name
            record.encrypted_access_token = encrypted_access_token
            record.encrypted_refresh_token = encrypted_refresh_token
            record.token_expires_at = token_expires_at
            record.scopes = scopes
            record.last_error_code = None
            record.last_error_message = None
            record.updated_at = datetime.now(tz=UTC)

        self._db.flush()
        self._db.refresh(record)
        return record

    def update_tokens(
        self,
        *,
        record: SpotifyConnectionRecord,
        encrypted_access_token: str,
        encrypted_refresh_token: str,
        token_expires_at: datetime,
    ) -> SpotifyConnectionRecord:
        """Persist refreshed Spotify tokens."""
        record.encrypted_access_token = encrypted_access_token
        record.encrypted_refresh_token = encrypted_refresh_token
        record.token_expires_at = token_expires_at
        record.last_error_code = None
        record.last_error_message = None
        record.updated_at = datetime.now(tz=UTC)
        self._db.flush()
        self._db.refresh(record)
        return record

    def mark_error(
        self,
        *,
        record: SpotifyConnectionRecord,
        error_code: str,
        error_message: str,
    ) -> SpotifyConnectionRecord:
        """Persist a refresh or token error on a connection."""
        record.last_error_code = error_code
        record.last_error_message = error_message
        record.updated_at = datetime.now(tz=UTC)
        self._db.flush()
        self._db.refresh(record)
        return record

    def delete_for_user(self, user_id: int) -> bool:
        """Remove a Spotify connection for a user."""
        record = self.get_for_user(user_id)
        if record is None:
            return False
        self._db.delete(record)
        self._db.flush()
        return True
