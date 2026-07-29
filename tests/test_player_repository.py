"""Unit tests for the in-memory player session repository."""

from musicbloom.models.player import (
    PlaybackState,
    Volume,
    create_initial_player_session,
)
from musicbloom.repositories.in_memory_player import InMemoryPlayerSessionRepository


def test_repository_returns_initial_session() -> None:
    repository = InMemoryPlayerSessionRepository()
    session = repository.get_session()

    assert session.state == PlaybackState.STOPPED
    assert session.volume.level == 0.8


def test_repository_save_and_get_round_trip() -> None:
    repository = InMemoryPlayerSessionRepository()
    session = create_initial_player_session()
    session.state = PlaybackState.PAUSED
    session.volume = Volume(level=0.5)

    saved = repository.save_session(session)
    loaded = repository.get_session()

    assert saved.state == PlaybackState.PAUSED
    assert loaded.volume.level == 0.5


def test_repository_reset_restores_defaults() -> None:
    repository = InMemoryPlayerSessionRepository()
    session = create_initial_player_session()
    session.state = PlaybackState.PLAYING
    repository.save_session(session)

    repository.reset()
    assert repository.get_session().state == PlaybackState.STOPPED
