"""Additional progression coverage tests."""

from datetime import UTC, datetime

import pytest
from sqlalchemy.orm import Session

from musicbloom.db.init import get_demo_user
from musicbloom.models.progression import ListeningEventType
from musicbloom.progression.policy import ProgressionPolicy
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
)


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


def test_require_for_user_raises_when_missing(db_session: Session) -> None:
    repository = UserProgressRepository(db_session)

    with pytest.raises(RuntimeError, match="User progress has not been initialized"):
        repository.require_for_user(999_999)


def test_submission_rejects_naive_datetime(
    progression_service: ProgressionService,
) -> None:
    with pytest.raises(InvalidListeningEventError, match="timezone-aware"):
        progression_service.submit_listening_event(
            track_id="demo-track-001",
            event_type=ListeningEventType.STARTED,
            position_ms=0,
            idempotency_key="naive-time",
            occurred_at=datetime(2026, 1, 1, 12, 0, 0),
        )


def test_progress_rejects_backward_seek(progression_service: ProgressionService) -> None:
    progression_service.submit_listening_event(
        track_id="demo-track-001",
        event_type=ListeningEventType.STARTED,
        position_ms=0,
        idempotency_key="backward-start",
    )
    progression_service.submit_listening_event(
        track_id="demo-track-001",
        event_type=ListeningEventType.PROGRESS,
        position_ms=60_000,
        idempotency_key="backward-progress",
    )

    with pytest.raises(InvalidListeningDurationError, match="cannot move backward"):
        progression_service.submit_listening_event(
            track_id="demo-track-001",
            event_type=ListeningEventType.PROGRESS,
            position_ms=30_000,
            idempotency_key="backward-invalid",
        )


def test_completion_can_apply_streak_without_new_progress(
    progression_service: ProgressionService,
) -> None:
    progression_service.submit_listening_event(
        track_id="demo-track-001",
        event_type=ListeningEventType.STARTED,
        position_ms=0,
        idempotency_key="completion-streak-start",
    )
    progression_service.submit_listening_event(
        track_id="demo-track-001",
        event_type=ListeningEventType.PROGRESS,
        position_ms=60_000,
        idempotency_key="completion-streak-progress",
    )
    completed = progression_service.submit_listening_event(
        track_id="demo-track-001",
        event_type=ListeningEventType.COMPLETED,
        position_ms=166_000,
        idempotency_key="completion-streak-complete",
    )

    assert any(award.reason.value == "track_completion" for award in completed.awards)


def test_policy_rejects_negative_position() -> None:
    policy = ProgressionPolicy()

    with pytest.raises(ValueError, match="cannot be negative"):
        policy.validate_position(position_ms=-1, track_duration_ms=184_000)


def test_policy_progress_award_returns_none_when_fully_capped() -> None:
    policy = ProgressionPolicy()

    assert (
        policy.calculate_progress_award(
            validated_delta_ms=120_000,
            progress_points_awarded=20,
            progress_experience_awarded=30,
        )
        is None
    )


def test_policy_streak_bonus_returns_none_when_daily_cap_reached() -> None:
    policy = ProgressionPolicy()

    assert (
        policy.calculate_streak_bonus(
            streak_days=4,
            bonus_awarded_today=50,
        )
        is None
    )


def test_policy_update_streak_without_meaningful_listen() -> None:
    policy = ProgressionPolicy()

    days, last_date = policy.update_streak(
        current_days=3,
        last_listening_utc_date=datetime(2026, 1, 1, tzinfo=UTC).date(),
        event_utc_date=datetime(2026, 1, 2, tzinfo=UTC).date(),
        meaningful_listen=False,
    )

    assert days == 3
    assert last_date == datetime(2026, 1, 1, tzinfo=UTC).date()


def test_unsupported_event_type_raises(progression_service: ProgressionService) -> None:
    class FakeEventType:
        value = "unsupported"

    with pytest.raises(InvalidListeningEventError, match="Unsupported event type"):
        progression_service._process_event(
            event_type=FakeEventType(),  # type: ignore[arg-type]
            position_ms=0,
            track_duration_ms=184_000,
            track_state=TrackListeningStateRepository(
                progression_service._track_states._db,
            ).get_or_create(
                user_id=progression_service._user_id,
                track_id="demo-track-001",
            ),
            progress=progression_service._progress.require_for_user(
                progression_service._user_id,
            ),
            event_id=1,
            track_id="demo-track-001",
            occurred_at=datetime.now(tz=UTC),
        )
