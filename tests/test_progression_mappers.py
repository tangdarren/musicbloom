"""Tests for progression mappers."""

from datetime import UTC, date, datetime

from musicbloom.db.mappers.progression import (
    build_daily_streak,
    build_listening_event_record,
    build_progress_summary,
    map_award_from_transaction,
    map_transaction,
)
from musicbloom.db.models.listening_event import ListeningEvent
from musicbloom.db.models.melody_points_transaction import MelodyPointsTransaction
from musicbloom.db.models.user_progress import UserProgress
from musicbloom.models.progression import ListeningEventType, PointsAwardReason


def test_progression_mappers_build_domain_models() -> None:
    progress = UserProgress(
        id=1,
        user_id=1,
        melody_points=10,
        level=2,
        total_listening_ms=60_000,
        experience_points=120,
        streak_current_days=2,
        streak_last_utc_date=date(2026, 1, 2),
        streak_bonus_points_today=10,
        streak_bonus_utc_date=date(2026, 1, 2),
    )
    event = ListeningEvent(
        id=7,
        user_id=1,
        track_id="demo-track-001",
        event_type="progress",
        position_ms=60_000,
        occurred_at=datetime(2026, 1, 2, 12, 0, 0, tzinfo=UTC),
        idempotency_key="mapper-key",
    )
    transaction = MelodyPointsTransaction(
        id=3,
        user_id=1,
        amount=4,
        experience_amount=6,
        reason="listening_progress",
        explanation="Mapper test",
        track_id="demo-track-001",
        listening_event_id=7,
        created_at=datetime(2026, 1, 2, 12, 0, 0, tzinfo=UTC),
    )

    summary = build_progress_summary(
        progress=progress,
        tracks_completed=1,
        total_listening_events=2,
    )
    streak = build_daily_streak(progress)
    record = build_listening_event_record(
        event=event,
        awards=[map_award_from_transaction(transaction)],
        melody_points_earned=4,
        experience_earned=6,
    )
    mapped_transaction = map_transaction(transaction)

    assert summary.level.level == 2
    assert streak.current_days == 2
    assert record.event_type is ListeningEventType.PROGRESS
    assert mapped_transaction.reason is PointsAwardReason.LISTENING_PROGRESS
