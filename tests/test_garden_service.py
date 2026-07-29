"""Tests for garden service logic."""


import pytest
from sqlalchemy.orm import Session

from musicbloom.db.init import get_demo_user
from musicbloom.models.garden import GardenMood
from musicbloom.repositories.achievement_progress import AchievementProgressRepository
from musicbloom.repositories.decoration_unlock import DecorationUnlockRepository
from musicbloom.repositories.demo_catalog import DemoCatalogRepository
from musicbloom.repositories.demo_rewards_catalog import DemoRewardsCatalogRepository
from musicbloom.repositories.equipped_decoration import EquippedDecorationRepository
from musicbloom.repositories.garden_profile import GardenProfileRepository
from musicbloom.repositories.track_listening_state import TrackListeningStateRepository
from musicbloom.repositories.user_progress import UserProgressRepository
from musicbloom.services.catalog import CatalogService
from musicbloom.services.garden import GardenService
from musicbloom.services.garden_errors import (
    DecorationLockedError,
    DecorationNotEquippedError,
    DecorationNotFoundError,
)


@pytest.fixture
def garden_service(db_session: Session) -> GardenService:
    user = get_demo_user(db_session)
    catalog = DemoCatalogRepository()
    rewards = DemoRewardsCatalogRepository()
    return GardenService(
        user_id=user.id,
        catalog_service=CatalogService(catalog),
        rewards_catalog=rewards,
        garden_profile_repository=GardenProfileRepository(db_session),
        equipped_decoration_repository=EquippedDecorationRepository(db_session),
        decoration_unlock_repository=DecorationUnlockRepository(db_session),
        user_progress_repository=UserProgressRepository(db_session),
        track_state_repository=TrackListeningStateRepository(db_session),
        achievement_progress_repository=AchievementProgressRepository(db_session),
    )


def test_get_garden_state_for_demo_user(garden_service: GardenService) -> None:
    state = garden_service.get_garden_state()

    assert state.profile.garden_name == "Starter Garden"
    assert state.tracks_completed == 0
    assert state.melody_points == 0


def test_list_decorations_marks_locked_items(garden_service: GardenService) -> None:
    decorations = garden_service.list_decorations()

    assert len(decorations) == 3
    assert all(not item.unlocked for item in decorations)


def test_equip_requires_unlock(
    db_session: Session,
    garden_service: GardenService,
) -> None:
    user = get_demo_user(db_session)

    with pytest.raises(DecorationLockedError):
        garden_service.equip_decoration("decoration-sprout-003")

    DecorationUnlockRepository(db_session).unlock(
        user_id=user.id,
        decoration_id="decoration-sprout-003",
    )

    result = garden_service.equip_decoration("decoration-sprout-003")
    assert result.slot == "south"


def test_unequip_requires_equipped_item(garden_service: GardenService) -> None:
    with pytest.raises(DecorationNotEquippedError):
        garden_service.unequip_decoration("decoration-sprout-003")


def test_artist_flowers_from_completed_tracks(
    db_session: Session,
    garden_service: GardenService,
) -> None:
    user = get_demo_user(db_session)
    track_repo = TrackListeningStateRepository(db_session)
    state = track_repo.get_or_create(user_id=user.id, track_id="demo-track-001")
    state.completion_awarded = True
    db_session.flush()

    flowers = garden_service.get_garden_state().artist_flowers

    assert len(flowers) == 1
    assert flowers[0].artist_name == "Petal & Pine"
    assert flowers[0].bloom_stage == 1


def test_recent_achievements_include_active_progress(
    db_session: Session,
    garden_service: GardenService,
) -> None:
    user = get_demo_user(db_session)
    achievement_repo = AchievementProgressRepository(db_session)
    record = achievement_repo.ensure_progress(
        user_id=user.id,
        achievement_id="achievement-first-bloom",
    )
    achievement_repo.save_progress(
        record=record,
        progress=1,
        completed=True,
    )

    recent = garden_service.get_garden_state().recent_achievements

    assert any(item.achievement_id == "achievement-first-bloom" for item in recent)


def test_equip_unknown_decoration_raises_not_found(
    garden_service: GardenService,
) -> None:
    with pytest.raises(DecorationNotFoundError):
        garden_service.equip_decoration("missing-decoration")


def test_unequip_unknown_decoration_raises_not_found(
    garden_service: GardenService,
) -> None:
    with pytest.raises(DecorationNotFoundError):
        garden_service.unequip_decoration("missing-decoration")


def test_streak_milestone_days(garden_service: GardenService) -> None:
    assert garden_service.streak_milestone_days() == (3, 7)


def test_blooming_mood_when_streak_is_active(
    db_session: Session,
    garden_service: GardenService,
) -> None:
    user = get_demo_user(db_session)
    progress = UserProgressRepository(db_session).require_for_user(user.id)
    progress.streak_current_days = 3
    db_session.flush()

    state = garden_service.get_garden_state()

    assert state.mood is GardenMood.BLOOMING


def test_list_decorations_marks_equipped_items(
    db_session: Session,
    garden_service: GardenService,
) -> None:
    user = get_demo_user(db_session)
    DecorationUnlockRepository(db_session).unlock(
        user_id=user.id,
        decoration_id="decoration-sprout-003",
    )
    EquippedDecorationRepository(db_session).equip(
        user_id=user.id,
        decoration_id="decoration-sprout-003",
        slot="south",
    )

    sprout = next(
        item
        for item in garden_service.list_decorations()
        if item.decoration.id == "decoration-sprout-003"
    )

    assert sprout.unlocked is True
    assert sprout.equipped is True

