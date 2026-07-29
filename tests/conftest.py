"""Shared pytest fixtures."""

from collections.abc import Generator, Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from musicbloom.api.app import create_app
from musicbloom.config import Settings
from musicbloom.db.init import get_demo_user, initialize_database
from musicbloom.db.mappers.player_session import (
    apply_player_session_to_record,
    create_default_player_session_record,
)
from musicbloom.db.models.player_session import PlayerSessionRecord
from musicbloom.db.session import create_test_database_engine, get_db
from musicbloom.dependencies import get_settings
from musicbloom.models.player import create_initial_player_session


@pytest.fixture(scope="session")
def test_engine() -> Engine:
    """Create a shared in-memory SQLite engine for tests."""
    engine = create_test_database_engine()
    initialize_database(engine, Settings(demo_mode=True))
    return engine


@pytest.fixture(scope="session")
def test_app(test_engine: Engine):
    """Create a FastAPI app bound to the shared test database."""
    settings = Settings(demo_mode=True)
    return create_app(settings=settings, engine=test_engine)


@pytest.fixture
def client(test_app) -> TestClient:
    """Return a test client for the configured application."""
    return TestClient(test_app)


@pytest.fixture
def db_session(test_engine: Engine) -> Generator[Session, None, None]:
    """Yield a database session bound to the test engine."""
    factory = sessionmaker(
        bind=test_engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@pytest.fixture(autouse=True)
def configure_test_dependencies(
    test_engine: Engine,
    test_app,
) -> Iterator[None]:
    """Wire request dependencies to the shared test database."""
    get_settings.cache_clear()
    factory = sessionmaker(
        bind=test_engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )

    def override_get_db() -> Generator[Session, None, None]:
        session = factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    test_app.dependency_overrides[get_db] = override_get_db
    _reset_demo_player_session(factory)
    yield
    test_app.dependency_overrides.clear()
    get_settings.cache_clear()


def _reset_demo_player_session(factory: sessionmaker[Session]) -> None:
    """Restore the demo user's player session to its initial state."""
    with factory() as session:
        user = get_demo_user(session)
        record = session.scalar(
            select(PlayerSessionRecord).where(
                PlayerSessionRecord.user_id == user.id,
            ),
        )
        initial = create_initial_player_session()
        if record is None:
            session.add(create_default_player_session_record(user.id))
        else:
            apply_player_session_to_record(record, initial)
        session.commit()
