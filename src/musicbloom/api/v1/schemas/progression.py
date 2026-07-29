"""Progression API request and response schemas."""

from datetime import datetime

from pydantic import BaseModel, Field

from musicbloom.models.progression import (
    DailyListeningStreak,
    ListeningEventRecord,
    ListeningEventType,
    ListeningStatistics,
    ProgressSummary,
)


class ListeningEventRequest(BaseModel):
    """Client-submitted listening event payload."""

    track_id: str = Field(description="Catalog track identifier")
    event_type: ListeningEventType = Field(description="Listening event type")
    position_ms: int = Field(
        ge=0,
        description="Playback position in milliseconds reported by the client",
    )
    idempotency_key: str = Field(
        min_length=1,
        max_length=64,
        description="Unique key to make this submission idempotent",
    )
    occurred_at: datetime | None = Field(
        default=None,
        description="UTC timestamp for the event; defaults to server time",
    )


ListeningEventResponse = ListeningEventRecord
ProgressSummaryResponse = ProgressSummary
ListeningStatisticsResponse = ListeningStatistics
DailyListeningStreakResponse = DailyListeningStreak
