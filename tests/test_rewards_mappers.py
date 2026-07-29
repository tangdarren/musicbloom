"""Tests for reward mappers."""

from datetime import UTC, datetime

import pytest

from musicbloom.db.mappers.rewards import (
    build_achievement_progress_view,
    build_quest_progress_view,
    build_reward_claim_record,
    derive_achievement_status,
    derive_quest_status,
)
from musicbloom.db.models.achievement_progress import AchievementProgress
from musicbloom.db.models.quest_progress import QuestProgress
from musicbloom.db.models.reward_claim import RewardClaim
from musicbloom.models.rewards import ProgressStatus
from musicbloom.repositories.demo_rewards_catalog import DemoRewardsCatalogRepository
from musicbloom.repositories.demo_rewards_data import (
    DEMO_ACHIEVEMENTS,
    DEMO_QUESTS,
    DEMO_REWARDS,
)


def test_reward_mappers_build_views() -> None:
    quest = DEMO_QUESTS[0]
    achievement = DEMO_ACHIEVEMENTS[0]
    reward = DEMO_REWARDS[0]
    quest_record = QuestProgress(
        id=1,
        user_id=1,
        quest_id=quest.id,
        status="active",
        progress=1,
        period_key="2026-01-01",
    )
    achievement_record = AchievementProgress(
        id=1,
        user_id=1,
        achievement_id=achievement.id,
        progress=1,
    )
    claim = RewardClaim(
        id=1,
        user_id=1,
        reward_id=reward.id,
        source_type="quest",
        source_id=quest.id,
        melody_points_granted=25,
        decoration_id=None,
        claimed_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    quest_view = build_quest_progress_view(
        quest=quest,
        reward=reward,
        record=quest_record,
        user_level=1,
    )
    achievement_view = build_achievement_progress_view(
        achievement=achievement,
        reward=reward,
        record=achievement_record,
        user_level=1,
    )
    claim_record = build_reward_claim_record(
        claim=claim,
        catalog=DemoRewardsCatalogRepository(),
    )

    assert quest_view.status is ProgressStatus.ACTIVE
    assert achievement_view.completion_percentage == 50.0
    assert claim_record.reward.id == reward.id
    assert (
        derive_quest_status(quest=quest, record=quest_record, user_level=1)
        is ProgressStatus.ACTIVE
    )
    inactive_record = QuestProgress(
        id=2,
        user_id=1,
        quest_id=quest.id,
        status="pending",
        progress=0,
        period_key="2026-01-01",
    )
    assert (
        derive_quest_status(quest=quest, record=inactive_record, user_level=1)
        is ProgressStatus.ACTIVE
    )
    assert (
        derive_achievement_status(
            achievement=achievement,
            record=achievement_record,
            user_level=0,
        )
        is ProgressStatus.LOCKED
    )
    claimed_achievement = AchievementProgress(
        id=2,
        user_id=1,
        achievement_id=achievement.id,
        progress=1,
        claimed_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    assert (
        derive_achievement_status(
            achievement=achievement,
            record=claimed_achievement,
            user_level=1,
        )
        is ProgressStatus.CLAIMED
    )


def test_build_reward_claim_record_raises_for_missing_reward() -> None:
    quest = DEMO_QUESTS[0]
    claim = RewardClaim(
        id=99,
        user_id=1,
        reward_id="missing-reward",
        source_type="quest",
        source_id=quest.id,
        melody_points_granted=0,
        decoration_id=None,
        claimed_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    with pytest.raises(RuntimeError, match="Reward 'missing-reward' was not found"):
        build_reward_claim_record(
            claim=claim,
            catalog=DemoRewardsCatalogRepository(),
        )
