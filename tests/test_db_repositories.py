"""Tests for gamification and profile repositories."""

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from musicbloom.db.init import get_demo_user
from musicbloom.repositories.achievement_progress import AchievementProgressRepository
from musicbloom.repositories.equipped_decoration import EquippedDecorationRepository
from musicbloom.repositories.garden_profile import GardenProfileRepository
from musicbloom.repositories.listening_event import ListeningEventRepository
from musicbloom.repositories.quest_progress import QuestProgressRepository
from musicbloom.repositories.user_profile import UserProfileRepository
from musicbloom.repositories.user_progress import UserProgressRepository


def test_user_profile_repository(db_session: Session) -> None:
    repository = UserProfileRepository(db_session)
    user = get_demo_user(db_session)

    assert repository.get_by_username("demo") is not None
    assert repository.get_by_id(user.id) is not None


def test_garden_and_progress_repositories(db_session: Session) -> None:
    user = get_demo_user(db_session)
    garden_repo = GardenProfileRepository(db_session)
    progress_repo = UserProgressRepository(db_session)

    garden = garden_repo.get_for_user(user.id)
    progress = progress_repo.get_for_user(user.id)

    assert garden is not None
    assert progress is not None
    assert progress.level == 1


def test_listening_event_repository(db_session: Session) -> None:
    user = get_demo_user(db_session)
    repository = ListeningEventRepository(db_session)

    repository.add_event(
        user_id=user.id,
        track_id="demo-track-001",
        event_type="play",
        position_ms=0,
        occurred_at=datetime.now(tz=UTC),
    )
    events = repository.list_for_user(user.id)

    assert len(events) == 1
    assert events[0].track_id == "demo-track-001"


def test_equipped_decoration_repository(db_session: Session) -> None:
    user = get_demo_user(db_session)
    repository = EquippedDecorationRepository(db_session)

    assert repository.list_for_user(user.id) == []

    first = repository.equip(
        user_id=user.id,
        decoration_id="lantern-001",
        slot="north",
    )
    second = repository.equip(
        user_id=user.id,
        decoration_id="fountain-002",
        slot="north",
    )

    assert first.id == second.id
    assert second.decoration_id == "fountain-002"


def test_achievement_and_quest_repositories(db_session: Session) -> None:
    user = get_demo_user(db_session)
    achievement_repo = AchievementProgressRepository(db_session)
    quest_repo = QuestProgressRepository(db_session)

    achievement_repo.upsert_progress(
        user_id=user.id,
        achievement_id="first-bloom",
        progress=1,
        completed=True,
    )
    quest_repo.upsert_progress(
        user_id=user.id,
        quest_id="water-the-garden",
        status="in_progress",
        progress=2,
    )
    updated_quest = quest_repo.upsert_progress(
        user_id=user.id,
        quest_id="water-the-garden",
        status="completed",
        progress=5,
        completed=True,
    )
    updated_achievement = achievement_repo.upsert_progress(
        user_id=user.id,
        achievement_id="first-bloom",
        progress=2,
        completed=False,
    )

    assert updated_quest.completed_at is not None
    assert updated_quest.status == "completed"
    assert updated_achievement.completed_at is None
    assert updated_achievement.progress == 2
