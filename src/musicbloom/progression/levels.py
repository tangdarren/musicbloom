"""Level and experience calculations."""

from musicbloom.models.progression import ExperienceProgress, UserLevel


def experience_required_for_next_level(current_level: int) -> int:
    """Return experience needed to advance from the current level."""
    if current_level < 1:
        msg = "Level must be at least 1"
        raise ValueError(msg)
    return 100 + (current_level - 1) * 50


def compute_user_level(total_experience: int) -> UserLevel:
    """Derive the current level from lifetime experience."""
    if total_experience < 0:
        msg = "Experience cannot be negative"
        raise ValueError(msg)

    level = 1
    remaining = total_experience
    while True:
        required = experience_required_for_next_level(level)
        if remaining < required:
            return UserLevel(
                level=level,
                experience=ExperienceProgress(
                    total_experience=total_experience,
                    experience_in_level=remaining,
                    experience_to_next_level=required,
                ),
            )
        remaining -= required
        level += 1
