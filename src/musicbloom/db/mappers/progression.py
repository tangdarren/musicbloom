"""Map progression ORM records to domain models."""

from musicbloom.db.models.listening_event import ListeningEvent
from musicbloom.db.models.melody_points_transaction import (
    MelodyPointsTransaction as MelodyPointsTransactionRecord,
)
from musicbloom.db.models.user_progress import UserProgress
from musicbloom.models.progression import (
    DailyListeningStreak,
    ListeningEventRecord,
    ListeningEventType,
    ListeningStatistics,
    MelodyPointsTransaction,
    PointsAwardExplanation,
    PointsAwardReason,
    ProgressSummary,
)
from musicbloom.progression.levels import compute_user_level
from musicbloom.progression.policy import ProgressionPolicy


def map_transaction(record: MelodyPointsTransactionRecord) -> MelodyPointsTransaction:
    """Convert a transaction ORM record to a domain model."""
    return MelodyPointsTransaction(
        id=record.id,
        amount=record.amount,
        reason=PointsAwardReason(record.reason),
        explanation=record.explanation,
        track_id=record.track_id,
        listening_event_id=record.listening_event_id,
        created_at=record.created_at,
    )


def map_award_from_transaction(
    record: MelodyPointsTransactionRecord,
) -> PointsAwardExplanation:
    """Convert a transaction record to an award explanation."""
    return PointsAwardExplanation(
        reason=PointsAwardReason(record.reason),
        melody_points=record.amount,
        experience=record.experience_amount,
        explanation=record.explanation,
    )


def build_daily_streak(progress: UserProgress) -> DailyListeningStreak:
    """Build streak domain model from user progress."""
    return DailyListeningStreak(
        current_days=progress.streak_current_days,
        last_listening_utc_date=progress.streak_last_utc_date,
        bonus_points_awarded_today=progress.streak_bonus_points_today,
        daily_bonus_cap=ProgressionPolicy.MAX_DAILY_STREAK_BONUS,
    )


def build_statistics(
    *,
    progress: UserProgress,
    tracks_completed: int,
    total_listening_events: int,
) -> ListeningStatistics:
    """Build listening statistics from stored progress."""
    return ListeningStatistics(
        total_listening_ms=progress.total_listening_ms,
        tracks_completed=tracks_completed,
        total_listening_events=total_listening_events,
        total_melody_points=progress.melody_points,
        total_experience=progress.experience_points,
    )


def build_progress_summary(
    *,
    progress: UserProgress,
    tracks_completed: int,
    total_listening_events: int,
) -> ProgressSummary:
    """Build the combined progress summary."""
    return ProgressSummary(
        melody_points=progress.melody_points,
        level=compute_user_level(progress.experience_points),
        streak=build_daily_streak(progress),
        statistics=build_statistics(
            progress=progress,
            tracks_completed=tracks_completed,
            total_listening_events=total_listening_events,
        ),
    )


def build_listening_event_record(
    *,
    event: ListeningEvent,
    awards: list[PointsAwardExplanation],
    melody_points_earned: int,
    experience_earned: int,
    duplicate: bool = False,
) -> ListeningEventRecord:
    """Build a listening event response model."""
    return ListeningEventRecord(
        id=event.id,
        idempotency_key=event.idempotency_key,
        track_id=event.track_id,
        event_type=ListeningEventType(event.event_type),
        position_ms=event.position_ms,
        occurred_at=event.occurred_at,
        awards=awards,
        melody_points_earned=melody_points_earned,
        experience_earned=experience_earned,
        duplicate=duplicate,
    )
