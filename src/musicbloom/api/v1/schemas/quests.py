"""Quest and achievement API schemas."""

from musicbloom.models.rewards import (
    AchievementProgressView,
    QuestProgressView,
    RewardClaimResult,
    RewardsInventory,
)

QuestListResponse = list[QuestProgressView]
AchievementListResponse = list[AchievementProgressView]
RewardClaimResponse = RewardClaimResult
RewardsInventoryResponse = RewardsInventory
