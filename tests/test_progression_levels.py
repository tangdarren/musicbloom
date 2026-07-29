"""Tests for progression level calculations."""

import pytest

from musicbloom.progression.levels import (
    compute_user_level,
    experience_required_for_next_level,
)


def test_experience_required_increases_gradually() -> None:
    assert experience_required_for_next_level(1) == 100
    assert experience_required_for_next_level(2) == 150
    assert experience_required_for_next_level(3) == 200


def test_compute_user_level_from_zero_experience() -> None:
    level = compute_user_level(0)

    assert level.level == 1
    assert level.experience.total_experience == 0
    assert level.experience.experience_in_level == 0
    assert level.experience.experience_to_next_level == 100


def test_compute_user_level_after_level_up_threshold() -> None:
    level = compute_user_level(100)

    assert level.level == 2
    assert level.experience.experience_in_level == 0
    assert level.experience.experience_to_next_level == 150


def test_compute_user_level_rejects_negative_experience() -> None:
    with pytest.raises(ValueError, match="Experience cannot be negative"):
        compute_user_level(-1)


def test_experience_required_rejects_invalid_level() -> None:
    with pytest.raises(ValueError, match="Level must be at least 1"):
        experience_required_for_next_level(0)
