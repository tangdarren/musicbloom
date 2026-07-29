"""Deterministic demo quest, achievement, and reward catalog data."""

from musicbloom.models.rewards import (
    AchievementDefinition,
    DecorationDefinition,
    ObjectiveType,
    QuestCadence,
    QuestDefinition,
    Reward,
    RewardType,
)

DEMO_REWARDS: tuple[Reward, ...] = (
    Reward(
        id="reward-daily-tracks",
        reward_type=RewardType.MELODY_POINTS,
        melody_points=25,
        description="25 Melody Points for completing three tracks",
    ),
    Reward(
        id="reward-daily-artists",
        reward_type=RewardType.DECORATION_UNLOCK,
        decoration_id="decoration-lantern-001",
        description="Unlock the Meadow Lantern decoration",
    ),
    Reward(
        id="reward-daily-minutes",
        reward_type=RewardType.MELODY_POINTS,
        melody_points=30,
        description="30 Melody Points for thirty minutes of listening",
    ),
    Reward(
        id="reward-weekly-streak",
        reward_type=RewardType.MELODY_POINTS,
        melody_points=40,
        description="40 Melody Points for maintaining a three-day streak",
    ),
    Reward(
        id="reward-weekly-genres",
        reward_type=RewardType.DECORATION_UNLOCK,
        decoration_id="decoration-fountain-002",
        description="Unlock the Bloom Fountain decoration",
    ),
    Reward(
        id="reward-weekly-focus",
        reward_type=RewardType.MELODY_POINTS,
        melody_points=50,
        description="50 Melody Points for a weekly focus session",
    ),
    Reward(
        id="reward-achievement-level-two",
        reward_type=RewardType.MELODY_POINTS,
        melody_points=75,
        description="75 Melody Points for reaching level 2",
    ),
    Reward(
        id="reward-achievement-first-bloom",
        reward_type=RewardType.DECORATION_UNLOCK,
        decoration_id="decoration-sprout-003",
        description="Unlock the First Sprout decoration",
    ),
)

DEMO_DECORATIONS: tuple[DecorationDefinition, ...] = (
    DecorationDefinition(
        id="decoration-lantern-001",
        name="Meadow Lantern",
        description="A soft lantern that glows after diverse listening sessions.",
        slot="north",
    ),
    DecorationDefinition(
        id="decoration-fountain-002",
        name="Bloom Fountain",
        description="A cheerful fountain earned by exploring multiple genres.",
        slot="center",
    ),
    DecorationDefinition(
        id="decoration-sprout-003",
        name="First Sprout",
        description="A starter sprout decoration for your first completed track.",
        slot="south",
    ),
)

DEMO_QUESTS: tuple[QuestDefinition, ...] = (
    QuestDefinition(
        id="daily-complete-three-tracks",
        title="Track Triad",
        description="Complete three tracks today.",
        cadence=QuestCadence.DAILY,
        objective_type=ObjectiveType.COMPLETE_TRACKS,
        target=3,
        reward_id="reward-daily-tracks",
    ),
    QuestDefinition(
        id="daily-three-artists",
        title="Artist Explorer",
        description="Listen to three different artists today.",
        cadence=QuestCadence.DAILY,
        objective_type=ObjectiveType.DISTINCT_ARTISTS,
        target=3,
        reward_id="reward-daily-artists",
    ),
    QuestDefinition(
        id="daily-thirty-minutes",
        title="Half-Hour Harmony",
        description="Listen for 30 valid minutes today.",
        cadence=QuestCadence.DAILY,
        objective_type=ObjectiveType.LISTENING_MINUTES,
        target=30,
        reward_id="reward-daily-minutes",
    ),
    QuestDefinition(
        id="weekly-three-day-streak",
        title="Steady Bloom",
        description="Maintain a three-day listening streak this week.",
        cadence=QuestCadence.WEEKLY,
        objective_type=ObjectiveType.STREAK_DAYS,
        target=3,
        reward_id="reward-weekly-streak",
    ),
    QuestDefinition(
        id="weekly-two-genres",
        title="Genre Gardener",
        description="Finish tracks from two genres this week.",
        cadence=QuestCadence.WEEKLY,
        objective_type=ObjectiveType.DISTINCT_GENRES,
        target=2,
        reward_id="reward-weekly-genres",
    ),
    QuestDefinition(
        id="weekly-focus-session",
        title="Weekly Focus Session",
        description="Complete 60 valid listening minutes this week.",
        cadence=QuestCadence.WEEKLY,
        objective_type=ObjectiveType.WEEKLY_FOCUS_MINUTES,
        target=60,
        reward_id="reward-weekly-focus",
    ),
)

DEMO_ACHIEVEMENTS: tuple[AchievementDefinition, ...] = (
    AchievementDefinition(
        id="achievement-reach-level-two",
        title="Level Up Listener",
        description="Reach MusicBloom level 2.",
        objective_type=ObjectiveType.LEVEL_REACHED,
        target=2,
        reward_id="reward-achievement-level-two",
    ),
    AchievementDefinition(
        id="achievement-first-bloom",
        title="First Bloom",
        description="Complete your first track.",
        objective_type=ObjectiveType.COMPLETE_TRACKS,
        target=1,
        reward_id="reward-achievement-first-bloom",
    ),
)
