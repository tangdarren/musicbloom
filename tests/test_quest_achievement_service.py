"""Tests for quest and achievement service behavior."""

from datetime import UTC, datetime

import pytest
from sqlalchemy.orm import Session

from musicbloom.db.init import get_demo_user
from musicbloom.models.progression import ListeningEventType
from musicbloom.models.rewards import ProgressStatus, QuestCadence
from musicbloom.repositories.achievement_progress import AchievementProgressRepository
from musicbloom.repositories.decoration_unlock import DecorationUnlockRepository
from musicbloom.repositories.demo_catalog import DemoCatalogRepository
from musicbloom.repositories.demo_rewards_catalog import DemoRewardsCatalogRepository
from musicbloom.repositories.listening_event import ListeningEventRepository
from musicbloom.repositories.quest_progress import QuestProgressRepository
from musicbloom.repositories.reward_claim import RewardClaimRepository
from musicbloom.repositories.track_listening_state import TrackListeningStateRepository
from musicbloom.repositories.user_progress import UserProgressRepository
from musicbloom.rewards.evaluator import period_key_for_cadence
from musicbloom.services.catalog import CatalogService
from musicbloom.services.quest_achievement import QuestAchievementService
from musicbloom.services.quest_errors import (
    AchievementNotFoundError,
    QuestNotFoundError,
    RewardAlreadyClaimedError,
    RewardNotClaimableError,
)

TRACK_ID = "demo-track-001"
COMPLETION_POSITION_MS = 166_000


@pytest.fixture
def quest_service(db_session: Session) -> QuestAchievementService:
    user = get_demo_user(db_session)
    return QuestAchievementService(
        user_id=user.id,
        catalog_service=CatalogService(DemoCatalogRepository()),
        rewards_catalog=DemoRewardsCatalogRepository(),
        quest_progress_repository=QuestProgressRepository(db_session),
        achievement_progress_repository=AchievementProgressRepository(db_session),
        reward_claim_repository=RewardClaimRepository(db_session),
        decoration_unlock_repository=DecorationUnlockRepository(db_session),
        listening_event_repository=ListeningEventRepository(db_session),
        track_state_repository=TrackListeningStateRepository(db_session),
        user_progress_repository=UserProgressRepository(db_session),
    )


def _complete_track(
    quest_service: QuestAchievementService,
    *,
    track_id: str,
    key_prefix: str,
) -> None:
    track = quest_service._catalog_service.get_track(track_id)
    assert track is not None
    track_state = quest_service._track_states.get_or_create(
        user_id=quest_service._user_id,
        track_id=track_id,
    )
    track_state.completion_awarded = True
    quest_service._track_states._db.flush()
    quest_service.evaluate_after_listening_event(
        track=track,
        event_type=ListeningEventType.COMPLETED,
        occurred_at=datetime.now(tz=UTC),
        validated_listening_delta_ms=0,
        completion_awarded=True,
    )
    quest_service._listening_events.add_event(
        user_id=quest_service._user_id,
        track_id=track_id,
        event_type="completed",
        idempotency_key=f"{key_prefix}-completed",
        position_ms=COMPLETION_POSITION_MS,
        occurred_at=datetime.now(tz=UTC),
    )


def test_list_quests_returns_seeded_entries(
    quest_service: QuestAchievementService,
) -> None:
    quest_service.seed_progress_records()
    quests = quest_service.list_quests()

    assert len(quests) == 6
    assert all(quest.status is ProgressStatus.ACTIVE for quest in quests)


def test_first_bloom_achievement_completes_on_track_completion(
    quest_service: QuestAchievementService,
) -> None:
    quest_service.seed_progress_records()
    _complete_track(quest_service, track_id=TRACK_ID, key_prefix="first-bloom")

    achievements = quest_service.list_achievements()
    first_bloom = next(
        item
        for item in achievements
        if item.achievement.id == "achievement-first-bloom"
    )

    assert first_bloom.status is ProgressStatus.COMPLETED
    assert first_bloom.progress == 1


def test_claim_quest_reward_grants_points(
    quest_service: QuestAchievementService,
) -> None:
    quest_service.seed_progress_records()
    period_key = period_key_for_cadence(QuestCadence.DAILY, datetime.now(tz=UTC))
    quest = quest_service._quest_progress.ensure_progress(
        user_id=quest_service._user_id,
        quest_id="daily-complete-three-tracks",
        period_key=period_key,
    )
    quest_service._quest_progress.save_progress(
        record=quest,
        status="completed",
        progress=3,
        completed=True,
    )

    result = quest_service.claim_quest("daily-complete-three-tracks")

    assert result.melody_points_granted == 25
    assert quest_service.get_rewards_inventory().total_claims == 1


def test_cannot_claim_incomplete_quest(quest_service: QuestAchievementService) -> None:
    quest_service.seed_progress_records()

    with pytest.raises(RewardNotClaimableError, match="not complete"):
        quest_service.claim_quest("daily-complete-three-tracks")


def test_cannot_claim_quest_twice(quest_service: QuestAchievementService) -> None:
    quest_service.seed_progress_records()
    period_key = period_key_for_cadence(QuestCadence.DAILY, datetime.now(tz=UTC))
    quest = quest_service._quest_progress.ensure_progress(
        user_id=quest_service._user_id,
        quest_id="daily-complete-three-tracks",
        period_key=period_key,
    )
    quest_service._quest_progress.save_progress(
        record=quest,
        status="completed",
        progress=3,
        completed=True,
    )
    quest_service.claim_quest("daily-complete-three-tracks")

    with pytest.raises(RewardAlreadyClaimedError):
        quest_service.claim_quest("daily-complete-three-tracks")


def test_claim_achievement_unlocks_decoration(
    quest_service: QuestAchievementService,
) -> None:
    quest_service.seed_progress_records()
    achievement = quest_service._achievement_progress.ensure_progress(
        user_id=quest_service._user_id,
        achievement_id="achievement-first-bloom",
    )
    quest_service._achievement_progress.save_progress(
        record=achievement,
        progress=1,
        completed=True,
    )

    result = quest_service.claim_achievement("achievement-first-bloom")

    assert result.decoration_unlocked is not None
    assert result.decoration_unlocked.id == "decoration-sprout-003"


def test_unknown_quest_and_achievement_raise_not_found(
    quest_service: QuestAchievementService,
) -> None:
    with pytest.raises(QuestNotFoundError):
        quest_service.claim_quest("missing-quest")

    with pytest.raises(AchievementNotFoundError):
        quest_service.claim_achievement("missing-achievement")
