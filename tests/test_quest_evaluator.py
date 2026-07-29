"""Tests for quest evaluation rules."""

from datetime import UTC, datetime

import pytest

from musicbloom.models.rewards import ObjectiveType, QuestCadence
from musicbloom.rewards.evaluator import (
    QuestEvaluationSnapshot,
    completion_percentage,
    compute_objective_progress,
    period_key_for_cadence,
)


def test_period_key_for_daily_and_weekly() -> None:
    moment = datetime(2026, 7, 28, 15, 0, 0, tzinfo=UTC)

    assert period_key_for_cadence(QuestCadence.DAILY, moment) == "2026-07-28"
    assert period_key_for_cadence(QuestCadence.WEEKLY, moment) == "2026-W31"


def test_completion_percentage_clamps_to_one_hundred() -> None:
    assert completion_percentage(3, 3) == 100.0
    assert completion_percentage(1, 4) == 25.0
    assert completion_percentage(1, 0) == 0.0


def test_compute_track_completion_for_daily_quests() -> None:
    snapshot = QuestEvaluationSnapshot(
        user_level=1,
        total_listening_ms=0,
        streak_days=0,
        tracks_completed_lifetime=0,
        distinct_artists_in_period=0,
        distinct_genres_in_period=0,
        weekly_focus_minutes=0,
        newly_completed_track=True,
        validated_listening_delta_ms=0,
    )

    progress = compute_objective_progress(
        objective_type=ObjectiveType.COMPLETE_TRACKS,
        target=3,
        snapshot=snapshot,
        current_progress=1,
        cadence=QuestCadence.DAILY,
    )

    assert progress == 2


def test_compute_listening_minutes_increments_with_delta() -> None:
    snapshot = QuestEvaluationSnapshot(
        user_level=1,
        total_listening_ms=0,
        streak_days=0,
        tracks_completed_lifetime=0,
        distinct_artists_in_period=0,
        distinct_genres_in_period=0,
        weekly_focus_minutes=0,
        validated_listening_delta_ms=120_000,
    )

    progress = compute_objective_progress(
        objective_type=ObjectiveType.LISTENING_MINUTES,
        target=30,
        snapshot=snapshot,
        current_progress=0,
        cadence=QuestCadence.DAILY,
    )

    assert progress == 2


def test_period_key_requires_timezone() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        period_key_for_cadence(
            QuestCadence.DAILY,
            datetime(2026, 1, 1, 12, 0, 0),
        )
