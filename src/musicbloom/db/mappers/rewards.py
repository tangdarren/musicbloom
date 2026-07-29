"""Map reward ORM records to domain models."""

from musicbloom.db.models.achievement_progress import AchievementProgress
from musicbloom.db.models.decoration_unlock import DecorationUnlockRecord
from musicbloom.db.models.quest_progress import QuestProgress
from musicbloom.db.models.reward_claim import RewardClaim
from musicbloom.models.rewards import (
    AchievementDefinition,
    AchievementProgressView,
    DecorationDefinition,
    DecorationUnlock,
    ProgressStatus,
    QuestDefinition,
    QuestProgressView,
    Reward,
    RewardClaimRecord,
)
from musicbloom.repositories.demo_rewards_catalog import DemoRewardsCatalogRepository
from musicbloom.rewards.evaluator import completion_percentage


def derive_quest_status(
    *,
    quest: QuestDefinition,
    record: QuestProgress,
    user_level: int,
) -> ProgressStatus:
    """Derive quest status from persisted progress."""
    if user_level < quest.unlock_level:
        return ProgressStatus.LOCKED
    if record.claimed_at is not None:
        return ProgressStatus.CLAIMED
    if record.progress >= quest.target or record.completed_at is not None:
        return ProgressStatus.COMPLETED
    if record.progress > 0 or record.status == "active":
        return ProgressStatus.ACTIVE
    return ProgressStatus.ACTIVE


def derive_achievement_status(
    *,
    achievement: AchievementDefinition,
    record: AchievementProgress,
    user_level: int,
) -> ProgressStatus:
    """Derive achievement status from persisted progress."""
    if user_level < achievement.unlock_level:
        return ProgressStatus.LOCKED
    if record.claimed_at is not None:
        return ProgressStatus.CLAIMED
    if record.progress >= achievement.target or record.completed_at is not None:
        return ProgressStatus.COMPLETED
    if record.progress > 0:
        return ProgressStatus.ACTIVE
    return ProgressStatus.ACTIVE


def build_quest_progress_view(
    *,
    quest: QuestDefinition,
    reward: Reward,
    record: QuestProgress,
    user_level: int,
) -> QuestProgressView:
    """Build a quest progress API model."""
    status = derive_quest_status(quest=quest, record=record, user_level=user_level)
    return QuestProgressView(
        quest=quest,
        reward=reward,
        status=status,
        progress=record.progress,
        target=quest.target,
        completion_percentage=completion_percentage(record.progress, quest.target),
        period_key=record.period_key,
        completed_at=record.completed_at,
        claimed_at=record.claimed_at,
    )


def build_achievement_progress_view(
    *,
    achievement: AchievementDefinition,
    reward: Reward,
    record: AchievementProgress,
    user_level: int,
) -> AchievementProgressView:
    """Build an achievement progress API model."""
    status = derive_achievement_status(
        achievement=achievement,
        record=record,
        user_level=user_level,
    )
    return AchievementProgressView(
        achievement=achievement,
        reward=reward,
        status=status,
        progress=record.progress,
        target=achievement.target,
        completion_percentage=completion_percentage(
            record.progress,
            achievement.target,
        ),
        completed_at=record.completed_at,
        claimed_at=record.claimed_at,
    )


def build_decoration_unlock(
    *,
    decoration: DecorationDefinition,
    record: DecorationUnlockRecord,
) -> DecorationUnlock:
    """Build a decoration unlock API model."""
    return DecorationUnlock(
        decoration=decoration,
        unlocked_at=record.unlocked_at,
    )


def build_reward_claim_record(
    *,
    claim: RewardClaim,
    catalog: DemoRewardsCatalogRepository,
) -> RewardClaimRecord:
    """Build a reward claim history API model."""
    reward = catalog.get_reward(claim.reward_id)
    if reward is None:
        msg = f"Reward '{claim.reward_id}' was not found"
        raise RuntimeError(msg)
    return RewardClaimRecord(
        id=claim.id,
        reward=reward,
        source_type=claim.source_type,
        source_id=claim.source_id,
        claimed_at=claim.claimed_at,
    )
