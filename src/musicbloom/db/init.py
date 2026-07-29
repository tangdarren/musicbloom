"""Explicit database initialization and demo seeding."""

from sqlalchemy import select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

import musicbloom.db.models  # noqa: F401
from musicbloom.config import Settings
from musicbloom.db.base import Base
from musicbloom.db.constants import (
    DEMO_DISPLAY_NAME,
    DEMO_GARDEN_NAME,
    DEMO_GARDEN_THEME,
    DEMO_USERNAME,
)
from musicbloom.db.mappers.player_session import create_default_player_session_record
from musicbloom.db.models.garden_profile import GardenProfile
from musicbloom.db.models.user_profile import UserProfile
from musicbloom.db.models.user_progress import UserProgress
from musicbloom.db.session import get_session_factory


def create_all_tables(engine: Engine) -> None:
    """Create all database tables on the supplied engine."""
    Base.metadata.create_all(bind=engine)


def seed_demo_user(session: Session) -> UserProfile:
    """Create or return the default demo user and related records."""
    existing = session.scalar(
        select(UserProfile).where(UserProfile.username == DEMO_USERNAME),
    )
    if existing is not None:
        return existing

    user = UserProfile(
        username=DEMO_USERNAME,
        display_name=DEMO_DISPLAY_NAME,
        avatar_url=None,
        is_demo_user=True,
    )
    session.add(user)
    session.flush()

    session.add(create_default_player_session_record(user.id))
    session.add(
        GardenProfile(
            user_id=user.id,
            garden_name=DEMO_GARDEN_NAME,
            theme=DEMO_GARDEN_THEME,
            layout_data={},
        ),
    )
    session.add(
        UserProgress(
            user_id=user.id,
            melody_points=0,
            level=1,
            total_listening_ms=0,
        ),
    )
    session.flush()
    return user


def initialize_database(engine: Engine, settings: Settings) -> None:
    """Initialize schema and optional demo seed data."""
    create_all_tables(engine)
    if settings.demo_mode:
        factory = get_session_factory(engine)
        with factory() as session:
            seed_demo_user(session)
            session.commit()


def get_demo_user(session: Session) -> UserProfile:
    """Return the demo user, raising if it has not been seeded."""
    user = session.scalar(
        select(UserProfile).where(UserProfile.username == DEMO_USERNAME),
    )
    if user is None:
        msg = "Demo user has not been seeded"
        raise RuntimeError(msg)
    return user
