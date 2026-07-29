"""Domain models for listening progression and rewards."""

from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class ListeningEventType(StrEnum):
    """Supported listening event types reported by the client."""

    STARTED = "started"
    PROGRESS = "progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"


class PointsAwardReason(StrEnum):
    """Reason codes stored with melody points transactions."""

    LISTENING_PROGRESS = "listening_progress"
    TRACK_COMPLETION = "track_completion"
    DAILY_STREAK = "daily_streak"


class PointsAwardExplanation(BaseModel):
    """Transparent explanation for a points or experience award."""

    reason: PointsAwardReason = Field(description="Machine-readable award reason")
    melody_points: int = Field(ge=0, description="Melody Points awarded")
    experience: int = Field(ge=0, description="Experience awarded")
    explanation: str = Field(description="Human-readable award explanation")


class MelodyPointsTransaction(BaseModel):
    """Recorded melody points change with audit metadata."""

    id: int = Field(description="Transaction identifier")
    amount: int = Field(description="Melody Points change amount")
    reason: PointsAwardReason = Field(description="Award reason code")
    explanation: str = Field(description="Human-readable award explanation")
    track_id: str | None = Field(default=None, description="Related track identifier")
    listening_event_id: int | None = Field(
        default=None,
        description="Related listening event identifier",
    )
    created_at: datetime = Field(
        description="UTC timestamp when the award was recorded",
    )


class ExperienceProgress(BaseModel):
    """Experience totals and progress toward the next level."""

    total_experience: int = Field(ge=0, description="Lifetime experience earned")
    experience_in_level: int = Field(
        ge=0,
        description="Experience earned within the current level",
    )
    experience_to_next_level: int = Field(
        ge=1,
        description="Experience required to reach the next level",
    )


class UserLevel(BaseModel):
    """Current player level derived from experience."""

    level: int = Field(ge=1, description="Current level")
    experience: ExperienceProgress = Field(description="Experience progress details")


class DailyListeningStreak(BaseModel):
    """UTC-based daily listening streak state."""

    current_days: int = Field(ge=0, description="Current consecutive listening days")
    last_listening_utc_date: date | None = Field(
        default=None,
        description="Last UTC date with meaningful listening",
    )
    bonus_points_awarded_today: int = Field(
        ge=0,
        description="Streak bonus Melody Points awarded today (UTC)",
    )
    daily_bonus_cap: int = Field(
        ge=0,
        description="Maximum streak bonus Melody Points per UTC day",
    )


class ListeningStatistics(BaseModel):
    """Aggregate listening metrics for the current user."""

    total_listening_ms: int = Field(ge=0, description="Validated listening time")
    tracks_completed: int = Field(ge=0, description="Tracks completed at least once")
    total_listening_events: int = Field(ge=0, description="Recorded listening events")
    total_melody_points: int = Field(ge=0, description="Current Melody Points balance")
    total_experience: int = Field(ge=0, description="Lifetime experience earned")


class ProgressSummary(BaseModel):
    """Combined progression snapshot for the current user."""

    melody_points: int = Field(ge=0, description="Current Melody Points balance")
    level: UserLevel = Field(description="Current level and experience progress")
    streak: DailyListeningStreak = Field(description="Daily listening streak state")
    statistics: ListeningStatistics = Field(description="Aggregate listening metrics")


class ListeningEventRecord(BaseModel):
    """Persisted listening event with optional awards."""

    id: int = Field(description="Listening event identifier")
    idempotency_key: str = Field(description="Client-supplied idempotency key")
    track_id: str = Field(description="Catalog track identifier")
    event_type: ListeningEventType = Field(description="Reported event type")
    position_ms: int = Field(ge=0, description="Playback position in milliseconds")
    occurred_at: datetime = Field(description="UTC timestamp when the event occurred")
    awards: list[PointsAwardExplanation] = Field(
        default_factory=list,
        description="Awards granted for this event",
    )
    melody_points_earned: int = Field(
        ge=0,
        description="Total Melody Points earned from this event",
    )
    experience_earned: int = Field(
        ge=0,
        description="Total experience earned from this event",
    )
    duplicate: bool = Field(
        default=False,
        description="Whether this response was replayed from an idempotent submission",
    )
