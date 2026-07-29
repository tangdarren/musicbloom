"""Additional database and session coverage tests."""

import pytest
from sqlalchemy.orm import Session

from musicbloom.config import Settings
from musicbloom.db.init import get_demo_user, initialize_database
from musicbloom.db.session import (
    create_test_database_engine,
    get_db,
    get_engine,
    get_session_factory,
    session_scope,
)
from musicbloom.repositories.database_player import DatabasePlayerSessionRepository
from musicbloom.repositories.garden_profile import GardenProfileRepository
from musicbloom.repositories.user_profile import UserProfileRepository
from musicbloom.repositories.user_progress import UserProgressRepository


def test_get_demo_user_raises_when_missing() -> None:
    engine = create_test_database_engine()
    initialize_database(engine, Settings(demo_mode=False))

    with session_scope(engine) as session, pytest.raises(
        RuntimeError,
        match="Demo user has not been seeded",
    ):
        get_demo_user(session)


def test_get_engine_and_session_helpers() -> None:
    get_engine.cache_clear()
    engine = get_engine()
    factory = get_session_factory(engine)
    session = factory()
    session.close()
    assert engine is get_engine()


def test_get_db_commits_successfully() -> None:
    get_engine.cache_clear()
    generator = get_db()
    session = next(generator)
    assert session is not None
    with pytest.raises(StopIteration):
        next(generator)


def test_get_db_rolls_back_on_error() -> None:
    get_engine.cache_clear()
    generator = get_db()
    next(generator)
    with pytest.raises(RuntimeError):
        generator.throw(RuntimeError("boom"))


def test_create_database_engine_uses_empty_connect_args_for_non_sqlite(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from sqlalchemy.pool import StaticPool

    from musicbloom.db.session import create_database_engine

    captured: dict[str, object] = {}

    def fake_create_engine(url: str, **kwargs: object):
        captured.update(kwargs)
        return __import__("sqlalchemy").create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )

    monkeypatch.setattr("musicbloom.db.session.create_engine", fake_create_engine)
    create_database_engine("postgresql://localhost/musicbloom")
    assert captured["connect_args"] == {}


def test_session_scope_rolls_back_on_error() -> None:
    engine = create_test_database_engine()
    with pytest.raises(ValueError), session_scope(engine):
        raise ValueError("force rollback")


def test_database_player_repository_creates_missing_record(
    db_session: Session,
) -> None:
    user = get_demo_user(db_session)
    db_session.execute(
        __import__("sqlalchemy").text("DELETE FROM player_sessions"),
    )
    db_session.commit()

    repository = DatabasePlayerSessionRepository(db_session, user.id)
    session = repository.get_session()
    assert session.state.value == "stopped"


def test_repository_add_helpers(db_session: Session) -> None:
    from musicbloom.db.models.garden_profile import GardenProfile
    from musicbloom.db.models.user_profile import UserProfile
    from musicbloom.db.models.user_progress import UserProgress

    user = UserProfile(
        username="extra-user",
        display_name="Extra",
        is_demo_user=False,
    )
    UserProfileRepository(db_session).add(user)
    GardenProfileRepository(db_session).add(
        GardenProfile(
            user_id=user.id,
            garden_name="Extra Garden",
            theme="meadow",
            layout_data={},
        ),
    )
    UserProgressRepository(db_session).add(
        UserProgress(user_id=user.id, melody_points=0, level=1, total_listening_ms=0),
    )

    assert user.id is not None
