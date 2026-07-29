"""Alembic migration tests."""

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect


def test_initial_migration_creates_schema(tmp_path: Path) -> None:
    database_path = tmp_path / "migration.db"
    database_url = f"sqlite:///{database_path}"
    engine = create_engine(database_url)

    alembic_cfg = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    alembic_cfg.set_main_option("sqlalchemy.url", database_url)

    command.upgrade(alembic_cfg, "head")

    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    assert "user_profiles" in tables
    assert "player_sessions" in tables
    assert "listening_events" in tables
    assert "garden_profiles" in tables
    assert "user_progress" in tables
    assert "equipped_decorations" in tables
    assert "achievement_progress" in tables
    assert "quest_progress" in tables
    assert "track_listening_states" in tables
    assert "melody_points_transactions" in tables
    assert "decoration_unlocks" in tables
    assert "reward_claims" in tables

    command.downgrade(alembic_cfg, "base")
    inspector = inspect(engine)
    assert "user_profiles" not in inspector.get_table_names()
