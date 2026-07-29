"""Database initialization tests."""

from sqlalchemy import select

from musicbloom.config import Settings
from musicbloom.db.constants import DEMO_USERNAME
from musicbloom.db.init import get_demo_user, initialize_database, seed_demo_user
from musicbloom.db.models.garden_profile import GardenProfile
from musicbloom.db.models.user_profile import UserProfile
from musicbloom.db.models.user_progress import UserProgress
from musicbloom.db.session import create_test_database_engine, session_scope


def test_initialize_database_seeds_demo_user_when_demo_mode_enabled() -> None:
    engine = create_test_database_engine()
    initialize_database(engine, Settings(demo_mode=True))

    with session_scope(engine) as session:
        user = get_demo_user(session)
        assert user.username == DEMO_USERNAME
        assert user.is_demo_user is True
        assert session.scalar(
            select(GardenProfile).where(GardenProfile.user_id == user.id),
        ) is not None
        assert session.scalar(
            select(UserProgress).where(UserProgress.user_id == user.id),
        ) is not None


def test_seed_demo_user_is_idempotent() -> None:
    engine = create_test_database_engine()
    initialize_database(engine, Settings(demo_mode=True))

    with session_scope(engine) as session:
        first = seed_demo_user(session)
        second = seed_demo_user(session)
        session.commit()
        assert first.id == second.id
        users = session.scalars(select(UserProfile)).all()
        assert len(users) == 1


def test_initialize_database_skips_demo_seed_when_disabled() -> None:
    engine = create_test_database_engine()
    initialize_database(engine, Settings(demo_mode=False))

    with session_scope(engine) as session:
        assert session.scalar(select(UserProfile)) is None
