"""Tests for deterministic progression policy rules."""

from datetime import UTC, date, datetime

import pytest

from musicbloom.models.progression import PointsAwardReason
from musicbloom.progression.policy import ProgressionPolicy


@pytest.fixture
def policy() -> ProgressionPolicy:
    return ProgressionPolicy()


def test_progress_award_returns_points_for_validated_intervals(
    policy: ProgressionPolicy,
) -> None:
    award = policy.calculate_progress_award(
        validated_delta_ms=60_000,
        progress_points_awarded=0,
        progress_experience_awarded=0,
    )

    assert award is not None
    assert award.melody_points == 4
    assert award.experience == 6


def test_progress_award_requires_interval(policy: ProgressionPolicy) -> None:
    assert (
        policy.calculate_progress_award(
            validated_delta_ms=29_999,
            progress_points_awarded=0,
            progress_experience_awarded=0,
        )
        is None
    )


def test_progress_award_respects_per_track_cap(policy: ProgressionPolicy) -> None:
    award = policy.calculate_progress_award(
        validated_delta_ms=600_000,
        progress_points_awarded=18,
        progress_experience_awarded=27,
    )

    assert award is not None
    assert award.melody_points == 2
    assert award.experience == 3


def test_completion_award_requires_threshold(policy: ProgressionPolicy) -> None:
    assert (
        policy.calculate_completion_award(
            position_ms=165_599,
            track_duration_ms=184_000,
            skipped=False,
            completion_awarded=False,
        )
        is None
    )


def test_completion_award_rejects_skipped_tracks(policy: ProgressionPolicy) -> None:
    assert (
        policy.calculate_completion_award(
            position_ms=184_000,
            track_duration_ms=184_000,
            skipped=True,
            completion_awarded=False,
        )
        is None
    )


def test_completion_award_is_not_repeated(policy: ProgressionPolicy) -> None:
    assert (
        policy.calculate_completion_award(
            position_ms=184_000,
            track_duration_ms=184_000,
            skipped=False,
            completion_awarded=True,
        )
        is None
    )


def test_completion_award_returns_bonus(policy: ProgressionPolicy) -> None:
    award = policy.calculate_completion_award(
        position_ms=184_000,
        track_duration_ms=184_000,
        skipped=False,
        completion_awarded=False,
    )

    assert award is not None
    assert award.melody_points == 15
    assert award.experience == 25
    assert award.reason is PointsAwardReason.TRACK_COMPLETION


def test_streak_bonus_is_capped_per_day(policy: ProgressionPolicy) -> None:
    first = policy.calculate_streak_bonus(streak_days=3, bonus_awarded_today=0)
    capped = policy.calculate_streak_bonus(streak_days=3, bonus_awarded_today=45)

    assert first is not None
    assert first.melody_points == 10
    assert capped is not None
    assert capped.melody_points == 5


def test_streak_bonus_not_awarded_without_streak(policy: ProgressionPolicy) -> None:
    assert policy.calculate_streak_bonus(streak_days=0, bonus_awarded_today=0) is None


def test_validate_position_rejects_invalid_duration(policy: ProgressionPolicy) -> None:
    with pytest.raises(ValueError, match="exceeds track duration"):
        policy.validate_position(position_ms=200_000, track_duration_ms=184_000)


def test_validate_progress_delta_rejects_backward_seek(policy: ProgressionPolicy) -> None:
    with pytest.raises(ValueError, match="cannot move backward"):
        policy.validate_progress_delta(
            position_ms=10_000,
            last_position_ms=20_000,
            track_duration_ms=184_000,
        )


def test_validate_progress_delta_rejects_large_jump(policy: ProgressionPolicy) -> None:
    with pytest.raises(ValueError, match="jump exceeds"):
        policy.validate_progress_delta(
            position_ms=70_000,
            last_position_ms=0,
            track_duration_ms=184_000,
        )


def test_update_streak_increments_on_consecutive_days(policy: ProgressionPolicy) -> None:
    days, last_date = policy.update_streak(
        current_days=2,
        last_listening_utc_date=date(2026, 1, 1),
        event_utc_date=date(2026, 1, 2),
        meaningful_listen=True,
    )

    assert days == 3
    assert last_date == date(2026, 1, 2)


def test_update_streak_resets_after_gap(policy: ProgressionPolicy) -> None:
    days, last_date = policy.update_streak(
        current_days=5,
        last_listening_utc_date=date(2026, 1, 1),
        event_utc_date=date(2026, 1, 3),
        meaningful_listen=True,
    )

    assert days == 1
    assert last_date == date(2026, 1, 3)


def test_utc_date_from_datetime_requires_timezone(policy: ProgressionPolicy) -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        policy.utc_date_from_datetime(datetime(2026, 1, 1, 12, 0, 0))


def test_utc_date_from_datetime_normalizes_to_utc(policy: ProgressionPolicy) -> None:
    value = datetime(2026, 1, 1, 20, 0, 0, tzinfo=UTC)
    assert policy.utc_date_from_datetime(value) == date(2026, 1, 1)
