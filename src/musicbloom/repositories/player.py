"""Player session persistence abstractions."""

from typing import Protocol

from musicbloom.models.player import PlayerSession


class PlayerSessionRepository(Protocol):
    """Persistence contract for player session state."""

    def get_session(self) -> PlayerSession:
        """Return the current player session."""

    def save_session(self, session: PlayerSession) -> PlayerSession:
        """Persist and return the updated player session."""
