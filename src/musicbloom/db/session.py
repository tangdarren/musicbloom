"""Database engine and session management."""

from collections.abc import Generator, Iterator
from contextlib import contextmanager
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from musicbloom.config import Settings


def create_database_engine(database_url: str) -> Engine:
    """Create a SQLAlchemy engine for the supplied URL."""
    connect_args: dict[str, object] = {}
    if database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    return create_engine(database_url, future=True, connect_args=connect_args)


def create_test_database_engine() -> Engine:
    """Create a shared in-memory SQLite engine for tests."""
    return create_engine(
        "sqlite://",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


@lru_cache
def get_engine() -> Engine:
    """Return a cached database engine."""
    settings = Settings()
    return create_database_engine(settings.resolved_database_url)


def get_session_factory(engine: Engine | None = None) -> sessionmaker[Session]:
    """Return a SQLAlchemy session factory."""
    return sessionmaker(
        bind=engine or get_engine(),
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )


@lru_cache
def get_sessionmaker() -> sessionmaker[Session]:
    """Return a cached session factory bound to the default engine."""
    return get_session_factory(get_engine())


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a request-scoped database session."""
    session = get_sessionmaker()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@contextmanager
def session_scope(engine: Engine | None = None) -> Iterator[Session]:
    """Provide a transactional scope for scripts and tests."""
    factory = get_session_factory(engine) if engine is not None else get_sessionmaker()
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
