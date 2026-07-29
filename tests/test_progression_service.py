"""Tests for progression service behavior."""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from musicbloom.db.init import get_demo_user
from musicbloom.models.progression import ListeningEventType, PointsAwardReason
from musicbloom.repositories.demo_catalog import DemoCatalogRepository
from musicbloom.repositories.listening_event import ListeningEventRepository
from musicbloom.repositories.melody_points_transaction import (
    MelodyPointsTransactionRepository,
)
from musicbloom.repositories.track_listening_state import TrackListeningStateRepository
from musicbloom.repositories.user_progress import UserProgressRepository
from musicbloom.services.catalog import CatalogService
from musicbloom.services.progression import ProgressionService
from musicbloom.services.progression_errors import (
    InvalidListeningDurationError,
    InvalidListeningEventError,
    TrackNotFoundError,
)

TRACK_ID = "demo-track-001"
TRACK_DURATION_MS = 184_000
COMPLETION_POSITION_MS = 166_000


@pytest.fixture
def progression_service(db_session: Session) -> ProgressionService:
    user = get_demo_user(db_session)
    return ProgressionService(
        user_id=user.id,
        catalog_service=CatalogService(DemoCatalogRepository()),
        listening_event_repository=ListeningEventRepository(db_session),
        track_state_repository=TrackListeningStateRepository(db_session),
        transaction_repository=MelodyPointsTransactionRepository(db_session),
        progress_repository=UserProgressRepository(db_session),
    )


def _submit(
    service: ProgressionService,
    *,
    event_type: ListeningEventType,
    position_ms: int,
    key: str,
    occurred_at: datetime | None = None,
):
    return service.submit_listening_event(
        track_id=TRACK_ID,
        event_type=event_type,
        position_ms=position_ms,
        idempotency_key=key,
        occurred_at=occurred_at,
    )


def test_started_event_awards_no_points(progression_service: ProgressionService) -> None:
    result = _submit(
        progression_service,
        event_type=ListeningEventType.STARTED,
        position_ms=0,
        key="start-1",
    )

    assert result.melody_points_earned == 0
    assert result.experience_earned == 0
    assert result.awards == []


def test_progress_event_awards_points_for_validated_intervals(
    progression_service: ProgressionService,
) -> None:
    _submit(
        progression_service,
        event_type=ListeningEventType.STARTED,
        position_ms=0,
        key="start-2",
    )
    result = _submit(
        progression_service,
        event_type=ListeningEventType.PROGRESS,
        position_ms=60_000,
        key="progress-1",
    )

    assert result.melody_points_earned >= 4
    assert result.experience_earned >= 6
    progress_awards = [
        award
        for award in result.awards
        if award.reason is PointsAwardReason.LISTENING_PROGRESS
    ]
    assert progress_awards[0].melody_points == 4


def test_completion_awards_bonus_once(progression_service: ProgressionService) -> None:
    _submit(
        progression_service,
        event_type=ListeningEventType.STARTED,
        position_ms=0,
        key="start-3",
    )
    _submit(
        progression_service,
        event_type=ListeningEventType.PROGRESS,
        position_ms=60_000,
        key="progress-2",
    )
    first = _submit(
        progression_service,
        event_type=ListeningEventType.COMPLETED,
        position_ms=COMPLETION_POSITION_MS,
        key="complete-1",
    )
    _submit(
        progression_service,
        event_type=ListeningEventType.STARTED,
        position_ms=0,
        key="start-4",
    )
    second = _submit(
        progression_service,
        event_type=ListeningEventType.COMPLETED,
        position_ms=COMPLETION_POSITION_MS,
        key="complete-2",
    )

    completion_awards = [
        award
        for award in first.awards
        if award.reason is PointsAwardReason.TRACK_COMPLETION
    ]
    repeat_completion_awards = [
        award
        for award in second.awards
        if award.reason is PointsAwardReason.TRACK_COMPLETION
    ]

    assert len(completion_awards) == 1
    assert completion_awards[0].melody_points == 15
    assert repeat_completion_awards == []


def test_skipped_track_cannot_complete(progression_service: ProgressionService) -> None:
    _submit(
        progression_service,
        event_type=ListeningEventType.STARTED,
        position_ms=0,
        key="start-5",
    )
    _submit(
        progression_service,
        event_type=ListeningEventType.SKIPPED,
        position_ms=30_000,
        key="skip-1",
    )

    with pytest.raises(InvalidListeningEventError, match="Skipped tracks"):
        _submit(
            progression_service,
            event_type=ListeningEventType.COMPLETED,
            position_ms=COMPLETION_POSITION_MS,
            key="complete-3",
        )


def test_skipped_track_cannot_earn_progress(progression_service: ProgressionService) -> None:
    _submit(
        progression_service,
        event_type=ListeningEventType.STARTED,
        position_ms=0,
        key="start-6",
    )
    _submit(
        progression_service,
        event_type=ListeningEventType.SKIPPED,
        position_ms=30_000,
        key="skip-2",
    )

    with pytest.raises(InvalidListeningEventError, match="Skipped tracks"):
        _submit(
            progression_service,
            event_type=ListeningEventType.PROGRESS,
            position_ms=60_000,
            key="progress-3",
        )


def test_invalid_position_rejected(progression_service: ProgressionService) -> None:
    with pytest.raises(InvalidListeningDurationError, match="exceeds track duration"):
        _submit(
            progression_service,
            event_type=ListeningEventType.STARTED,
            position_ms=TRACK_DURATION_MS + 1,
            key="invalid-position",
        )


def test_idempotent_submission_returns_duplicate_response(
    progression_service: ProgressionService,
) -> None:
    _submit(
        progression_service,
        event_type=ListeningEventType.STARTED,
        position_ms=0,
        key="start-7",
    )
    first = _submit(
        progression_service,
        event_type=ListeningEventType.PROGRESS,
        position_ms=60_000,
        key="duplicate-key",
    )
    second = _submit(
        progression_service,
        event_type=ListeningEventType.PROGRESS,
        position_ms=60_000,
        key="duplicate-key",
    )

    assert first.duplicate is False
    assert second.duplicate is True
    assert second.melody_points_earned == first.melody_points_earned
    assert second.experience_earned == first.experience_earned


def test_unknown_track_returns_not_found(progression_service: ProgressionService) -> None:
    with pytest.raises(TrackNotFoundError):
        progression_service.submit_listening_event(
            track_id="missing-track",
            event_type=ListeningEventType.STARTED,
            position_ms=0,
            idempotency_key="missing-track",
        )


def test_meaningful_listen_updates_streak(progression_service: ProgressionService) -> None:
    day_one = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)
    day_two = day_one + timedelta(days=1)

    _submit(
        progression_service,
        event_type=ListeningEventType.STARTED,
        position_ms=0,
        key="streak-start-1",
        occurred_at=day_one,
    )
    _submit(
        progression_service,
        event_type=ListeningEventType.PROGRESS,
        position_ms=60_000,
        key="streak-progress-1",
        occurred_at=day_one,
    )
    _submit(
        progression_service,
        event_type=ListeningEventType.STARTED,
        position_ms=0,
        key="streak-start-2",
        occurred_at=day_two,
    )
    _submit(
        progression_service,
        event_type=ListeningEventType.PROGRESS,
        position_ms=60_000,
        key="streak-progress-2",
        occurred_at=day_two,
    )

    streak = progression_service.get_streak()

    assert streak.current_days == 2
    assert streak.last_listening_utc_date == day_two.date()


def test_level_increases_after_enough_experience(
    progression_service: ProgressionService,
) -> None:
    scenarios = [
        ("demo-track-001", 120_000, 166_000),
        ("demo-track-002", 120_000, 190_000),
        ("demo-track-003", 120_000, 221_000),
    ]

    for index, (track_id, progress_position, completion_position) in enumerate(
        scenarios,
    ):
        progression_service.submit_listening_event(
            track_id=track_id,
            event_type=ListeningEventType.STARTED,
            position_ms=0,
            idempotency_key=f"level-start-{index}",
        )
        progression_service.submit_listening_event(
            track_id=track_id,
            event_type=ListeningEventType.PROGRESS,
            position_ms=60_000,
            idempotency_key=f"level-progress-a-{index}",
        )
        progression_service.submit_listening_event(
            track_id=track_id,
            event_type=ListeningEventType.PROGRESS,
            position_ms=progress_position,
            idempotency_key=f"level-progress-b-{index}",
        )
        progression_service.submit_listening_event(
            track_id=track_id,
            event_type=ListeningEventType.COMPLETED,
            position_ms=completion_position,
            idempotency_key=f"level-complete-{index}",
        )

    summary = progression_service.get_progress_summary()

    assert summary.level.level >= 2


def test_progress_summary_and_statistics(progression_service: ProgressionService) -> None:
    _submit(
        progression_service,
        event_type=ListeningEventType.STARTED,
        position_ms=0,
        key="summary-start",
    )
    _submit(
        progression_service,
        event_type=ListeningEventType.PROGRESS,
        position_ms=60_000,
        key="summary-progress",
    )

    summary = progression_service.get_progress_summary()
    stats = progression_service.get_statistics()

    assert summary.melody_points == stats.total_melody_points
    assert summary.statistics.total_listening_events == stats.total_listening_events
    assert stats.total_listening_ms == 60_000
