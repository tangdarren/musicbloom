"""Quest and achievement routes."""

from fastapi import APIRouter

from musicbloom.api.v1.schemas.quests import (
    AchievementListResponse,
    QuestListResponse,
    RewardClaimResponse,
    RewardsInventoryResponse,
)
from musicbloom.dependencies import QuestAchievementServiceDep

router = APIRouter(tags=["quests"])


@router.get(
    "/quests",
    response_model=QuestListResponse,
    summary="List quests",
    description="Return daily and weekly quests with progress totals and statuses.",
)
def list_quests(
    quest_service: QuestAchievementServiceDep,
) -> QuestListResponse:
    """Return quest progress for the current user."""
    return quest_service.list_quests()


@router.get(
    "/achievements",
    response_model=AchievementListResponse,
    summary="List achievements",
    description="Return achievements with progress totals and statuses.",
)
def list_achievements(
    quest_service: QuestAchievementServiceDep,
) -> AchievementListResponse:
    """Return achievement progress for the current user."""
    return quest_service.list_achievements()


@router.post(
    "/quests/{quest_id}/claim",
    response_model=RewardClaimResponse,
    summary="Claim a quest reward",
    description="Claim the reward for a completed quest.",
)
def claim_quest(
    quest_id: str,
    quest_service: QuestAchievementServiceDep,
) -> RewardClaimResponse:
    """Claim a quest reward when the quest is complete."""
    return quest_service.claim_quest(quest_id)


@router.post(
    "/achievements/{achievement_id}/claim",
    response_model=RewardClaimResponse,
    summary="Claim an achievement reward",
    description="Claim the reward for a completed achievement.",
)
def claim_achievement(
    achievement_id: str,
    quest_service: QuestAchievementServiceDep,
) -> RewardClaimResponse:
    """Claim an achievement reward when the achievement is complete."""
    return quest_service.claim_achievement(achievement_id)


@router.get(
    "/rewards",
    response_model=RewardsInventoryResponse,
    summary="List rewards inventory",
    description="Return unlocked decorations and reward claim history.",
)
def list_rewards(
    quest_service: QuestAchievementServiceDep,
) -> RewardsInventoryResponse:
    """Return the current user's reward inventory."""
    return quest_service.get_rewards_inventory()
