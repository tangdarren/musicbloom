"""Domain models for quests, achievements, and rewards."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field, computed_field


class QuestCadence(StrEnum):
    """Quest reset cadence."""

    DAILY = "daily"
    WEEKLY = "weekly"


class ObjectiveType(StrEnum):
    """Supported quest and achievement objective types."""

    COMPLETE_TRACKS = "complete_tracks"
    DISTINCT_ARTISTS = "distinct_artists"
    LISTENING_MINUTES = "listening_minutes"
    STREAK_DAYS = "streak_days"
    DISTINCT_GENRES = "distinct_genres"
    LEVEL_REACHED = "level_reached"
    WEEKLY_FOCUS_MINUTES = "weekly_focus_minutes"


class RewardType(StrEnum):
    """Reward grant types."""

    MELODY_POINTS = "melody_points"
    DECORATION_UNLOCK = "decoration_unlock"


class ProgressStatus(StrEnum):
    """Quest and achievement lifecycle states."""

    LOCKED = "locked"
    ACTIVE = "active"
    COMPLETED = "completed"
    CLAIMED = "claimed"


class Reward(BaseModel):
    """Reward granted by completing a quest or achievement."""

    id: str = Field(description="Stable reward identifier")
    reward_type: RewardType = Field(description="Reward category")
    melody_points: int = Field(
        ge=0,
        default=0,
        description="Melody Points granted when applicable",
    )
    decoration_id: str | None = Field(
        default=None,
        description="Decoration unlocked when applicable",
    )
    description: str = Field(description="Human-readable reward description")


class DecorationDefinition(BaseModel):
    """Unlockable garden decoration metadata."""

    id: str = Field(description="Stable decoration identifier")
    name: str = Field(description="Display name")
    description: str = Field(description="Decoration description")
    slot: str = Field(description="Default garden slot for the decoration")


class QuestDefinition(BaseModel):
    """Static quest definition from the demo catalog."""

    id: str = Field(description="Stable quest identifier")
    title: str = Field(description="Quest title")
    description: str = Field(description="Quest description")
    cadence: QuestCadence = Field(description="Quest reset cadence")
    objective_type: ObjectiveType = Field(description="Objective tracked by the quest")
    target: int = Field(ge=1, description="Objective target value")
    reward_id: str = Field(description="Associated reward identifier")
    unlock_level: int = Field(
        ge=1,
        default=1,
        description="Minimum user level required to activate the quest",
    )


class AchievementDefinition(BaseModel):
    """Static achievement definition from the demo catalog."""

    id: str = Field(description="Stable achievement identifier")
    title: str = Field(description="Achievement title")
    description: str = Field(description="Achievement description")
    objective_type: ObjectiveType = Field(
        description="Objective tracked by the achievement",
    )
    target: int = Field(ge=1, description="Objective target value")
    reward_id: str = Field(description="Associated reward identifier")
    unlock_level: int = Field(
        ge=1,
        default=1,
        description="Minimum user level required to activate the achievement",
    )


class QuestProgressView(BaseModel):
    """Quest progress returned by the API."""

    quest: QuestDefinition = Field(description="Quest definition")
    reward: Reward = Field(description="Quest reward")
    status: ProgressStatus = Field(description="Current quest status")
    progress: int = Field(ge=0, description="Current progress total")
    target: int = Field(ge=1, description="Objective target")
    completion_percentage: float = Field(
        ge=0,
        le=100,
        description="Completion percentage toward the objective",
    )
    period_key: str = Field(description="Active reset period identifier")
    completed_at: datetime | None = Field(default=None)
    claimed_at: datetime | None = Field(default=None)


class AchievementProgressView(BaseModel):
    """Achievement progress returned by the API."""

    achievement: AchievementDefinition = Field(description="Achievement definition")
    reward: Reward = Field(description="Achievement reward")
    status: ProgressStatus = Field(description="Current achievement status")
    progress: int = Field(ge=0, description="Current progress total")
    target: int = Field(ge=1, description="Objective target")
    completion_percentage: float = Field(
        ge=0,
        le=100,
        description="Completion percentage toward the objective",
    )
    completed_at: datetime | None = Field(default=None)
    claimed_at: datetime | None = Field(default=None)


class DecorationUnlock(BaseModel):
    """Decoration unlocked for the current user."""

    decoration: DecorationDefinition = Field(description="Decoration metadata")
    unlocked_at: datetime = Field(description="UTC unlock timestamp")


class RewardClaimRecord(BaseModel):
    """Historical reward claim entry."""

    id: int = Field(description="Claim record identifier")
    reward: Reward = Field(description="Claimed reward")
    source_type: str = Field(description="Quest or achievement source type")
    source_id: str = Field(description="Quest or achievement identifier")
    claimed_at: datetime = Field(description="UTC claim timestamp")


class RewardClaimResult(BaseModel):
    """Result of claiming a quest or achievement reward."""

    source_type: str = Field(description="Quest or achievement source type")
    source_id: str = Field(description="Quest or achievement identifier")
    reward: Reward = Field(description="Claimed reward")
    melody_points_granted: int = Field(ge=0, description="Melody Points granted")
    decoration_unlocked: DecorationDefinition | None = Field(default=None)
    claimed_at: datetime = Field(description="UTC claim timestamp")


class RewardsInventory(BaseModel):
    """Combined reward and unlock inventory for the current user."""

    melody_points: int = Field(ge=0, description="Current Melody Points balance")
    unlocked_decorations: list[DecorationUnlock] = Field(
        default_factory=list,
        description="Decorations unlocked by the user",
    )
    claim_history: list[RewardClaimRecord] = Field(
        default_factory=list,
        description="Historical reward claims",
    )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def total_claims(self) -> int:
        """Return the number of recorded reward claims."""
        return len(self.claim_history)
