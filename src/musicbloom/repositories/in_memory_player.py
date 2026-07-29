"""In-memory player session repository."""

from musicbloom.models.player import PlayerSession, create_initial_player_session


class InMemoryPlayerSessionRepository:
    """Mutable in-memory store for a single player session."""

    def __init__(self, session: PlayerSession | None = None) -> None:
        self._session = session or create_initial_player_session()

    def get_session(self) -> PlayerSession:
        """Return the current player session."""
        return self._session.model_copy(deep=True)

    def save_session(self, session: PlayerSession) -> PlayerSession:
        """Persist and return the updated player session."""
        self._session = session.model_copy(deep=True)
        return self.get_session()

    def reset(self) -> None:
        """Restore the repository to its initial session state."""
        self._session = create_initial_player_session()
