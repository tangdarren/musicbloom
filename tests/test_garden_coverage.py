"""Additional garden service coverage tests."""

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session

from musicbloom.db.constants import DEMO_GARDEN_NAME, DEMO_GARDEN_THEME
from musicbloom.db.init import get_demo_user
from musicbloom.db.models.decoration_unlock import DecorationUnlockRecord
from musicbloom.db.models.equipped_decoration import EquippedDecoration
from musicbloom.db.models.garden_profile import GardenProfile
from musicbloom.models.rewards import AchievementDefinition, ObjectiveType
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
from musicbloom.services.garden_errors import GardenProfileNotFoundError


@pytest.fixture
def garden_service(db_session: Session) -> GardenService:
    user = get_demo_user(db_session)
    return GardenService(
        user_id=user.id,
        catalog_service=CatalogService(DemoCatalogRepository()),
        rewards_catalog=DemoRewardsCatalogRepository(),
        garden_profile_repository=GardenProfileRepository(db_session),
        equipped_decoration_repository=EquippedDecorationRepository(db_session),
        decoration_unlock_repository=DecorationUnlockRepository(db_session),
        user_progress_repository=UserProgressRepository(db_session),
        track_state_repository=TrackListeningStateRepository(db_session),
        achievement_progress_repository=AchievementProgressRepository(db_session),
    )


def test_garden_profile_not_found(
    db_session: Session,
    garden_service: GardenService,
) -> None:
    user = get_demo_user(db_session)
    profile = GardenProfileRepository(db_session).get_for_user(user.id)
    assert profile is not None
    db_session.delete(profile)
    db_session.flush()

    with pytest.raises(GardenProfileNotFoundError):
        garden_service.get_garden_state()

    db_session.add(
        GardenProfile(
            user_id=user.id,
            garden_name=DEMO_GARDEN_NAME,
            theme=DEMO_GARDEN_THEME,
            layout_data={},
        ),
    )
    db_session.flush()


def test_artist_flowers_skip_unknown_tracks(
    db_session: Session,
    garden_service: GardenService,
) -> None:
    user = get_demo_user(db_session)
    state = TrackListeningStateRepository(db_session).get_or_create(
        user_id=user.id,
        track_id="missing-track-id",
    )
    state.completion_awarded = True
    db_session.flush()

    assert garden_service._build_artist_flowers() == []


def test_unlocked_and_equipped_decorations_skip_unknown_catalog_ids(
    db_session: Session,
    garden_service: GardenService,
) -> None:
    user = get_demo_user(db_session)
    now = datetime.now(tz=UTC)
    db_session.add(
        DecorationUnlockRecord(
            user_id=user.id,
            decoration_id="missing-decoration",
            unlocked_at=now,
        ),
    )
    db_session.add(
        EquippedDecoration(
            user_id=user.id,
            decoration_id="missing-decoration",
            slot="north",
            equipped_at=now,
        ),
    )
    db_session.flush()

    assert garden_service._build_unlocked_decorations() == []
    assert garden_service._build_equipped_decorations() == []


def test_recent_achievements_skip_missing_rewards_and_locked_entries(
    garden_service: GardenService,
) -> None:
    rewards_catalog = DemoRewardsCatalogRepository()
    valid_achievement = rewards_catalog.list_achievements()[0]
    locked_achievement = AchievementDefinition(
        id="achievement-locked-demo",
        title="Locked Demo",
        description="Requires a higher level.",
        objective_type=ObjectiveType.COMPLETE_TRACKS,
        target=1,
        reward_id=valid_achievement.reward_id,
        unlock_level=99,
    )
    missing_reward_achievement = AchievementDefinition(
        id="achievement-missing-reward",
        title="Missing Reward",
        description="Has no reward definition.",
        objective_type=ObjectiveType.COMPLETE_TRACKS,
        target=1,
        reward_id="missing-reward-id",
    )

    def list_achievements():
        return [locked_achievement, missing_reward_achievement, valid_achievement]

    mock_catalog = MagicMock(wraps=rewards_catalog)
    mock_catalog.list_achievements.side_effect = list_achievements
    def resolve_reward(reward_id: str):
        if reward_id == "missing-reward-id":
            return None
        return rewards_catalog.get_reward(reward_id)

    mock_catalog.get_reward.side_effect = resolve_reward

    garden_service._rewards_catalog = mock_catalog

    recent = garden_service._build_recent_achievements(user_level=1)

    excluded = {"achievement-locked-demo", "achievement-missing-reward"}
    assert all(item.achievement_id not in excluded for item in recent)


def test_artist_flowers_skip_missing_artist_names(
    garden_service: GardenService,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeCounter:
        def most_common(self, _limit: int):
            return [("ghost-artist", 2)]

    monkeypatch.setattr(
        "musicbloom.services.garden.Counter",
        lambda _values=None: FakeCounter(),
    )
    monkeypatch.setattr(
        garden_service._track_states,
        "list_completed_track_ids_for_user",
        lambda _user_id: ["ignored-track"],
    )

    assert garden_service._build_artist_flowers() == []
