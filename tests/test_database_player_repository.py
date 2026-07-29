"""Tests for the database-backed player session repository."""

from sqlalchemy.orm import Session

from musicbloom.db.init import get_demo_user
from musicbloom.models.player import PlaybackState
from musicbloom.repositories.database_player import DatabasePlayerSessionRepository
from musicbloom.repositories.demo_catalog import DemoCatalogRepository
from musicbloom.services.player import PlayerService


def test_database_player_repository_persists_session(db_session: Session) -> None:
    repository = DatabasePlayerSessionRepository.for_demo_user(db_session)
    service = PlayerService(repository, DemoCatalogRepository())

    session = service.play(track_id="demo-track-001")
    assert session.state == PlaybackState.PLAYING

    reloaded = DatabasePlayerSessionRepository.for_demo_user(db_session)
    persisted = reloaded.get_session()
    assert persisted.active_track is not None
    assert persisted.active_track.track_id == "demo-track-001"


def test_database_player_repository_scoped_to_demo_user(db_session: Session) -> None:
    user = get_demo_user(db_session)
    repository = DatabasePlayerSessionRepository(db_session, user.id)

    session = repository.get_session()
    assert session.state == PlaybackState.STOPPED
    assert session.volume.level == 0.8

    session.state = PlaybackState.PAUSED
    repository.save_session(session)
    reloaded = repository.get_session()
    assert reloaded.state == PlaybackState.PAUSED
