"""In-memory demo quest and achievement catalog."""

from musicbloom.models.rewards import (
    AchievementDefinition,
    DecorationDefinition,
    QuestDefinition,
    Reward,
)
from musicbloom.repositories.demo_rewards_data import (
    DEMO_ACHIEVEMENTS,
    DEMO_DECORATIONS,
    DEMO_QUESTS,
    DEMO_REWARDS,
)


class DemoRewardsCatalogRepository:
    """Read-only repository for seeded quests, achievements, and rewards."""

    def list_quests(self) -> list[QuestDefinition]:
        """Return all demo quest definitions."""
        return list(DEMO_QUESTS)

    def get_quest(self, quest_id: str) -> QuestDefinition | None:
        """Return a quest definition by identifier."""
        return next((quest for quest in DEMO_QUESTS if quest.id == quest_id), None)

    def list_achievements(self) -> list[AchievementDefinition]:
        """Return all demo achievement definitions."""
        return list(DEMO_ACHIEVEMENTS)

    def get_achievement(self, achievement_id: str) -> AchievementDefinition | None:
        """Return an achievement definition by identifier."""
        return next(
            (
                achievement
                for achievement in DEMO_ACHIEVEMENTS
                if achievement.id == achievement_id
            ),
            None,
        )

    def get_reward(self, reward_id: str) -> Reward | None:
        """Return a reward definition by identifier."""
        return next((reward for reward in DEMO_REWARDS if reward.id == reward_id), None)

    def get_decoration(self, decoration_id: str) -> DecorationDefinition | None:
        """Return a decoration definition by identifier."""
        return next(
            (
                decoration
                for decoration in DEMO_DECORATIONS
                if decoration.id == decoration_id
            ),
            None,
        )

    def list_decorations(self) -> list[DecorationDefinition]:
        """Return all demo decoration definitions."""
        return list(DEMO_DECORATIONS)
