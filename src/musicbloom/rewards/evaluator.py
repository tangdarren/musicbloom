"""Quest evaluation logic separated from API routes."""

from dataclasses import dataclass
from datetime import UTC, datetime

from musicbloom.models.rewards import ObjectiveType, QuestCadence


@dataclass(frozen=True, slots=True)
class QuestEvaluationSnapshot:
    """Validated inputs used to evaluate quest and achievement progress."""

    user_level: int
    total_listening_ms: int
    streak_days: int
    tracks_completed_lifetime: int
    distinct_artists_in_period: int
    distinct_genres_in_period: int
    weekly_focus_minutes: int
    newly_completed_track: bool = False
    validated_listening_delta_ms: int = 0


def period_key_for_cadence(cadence: QuestCadence, moment: datetime) -> str:
    """Return the reset period key for a quest cadence."""
    if moment.tzinfo is None:
        msg = "Datetime must be timezone-aware"
        raise ValueError(msg)
    utc_moment = moment.astimezone(UTC)
    if cadence is QuestCadence.DAILY:
        return utc_moment.date().isoformat()
    year, week, _ = utc_moment.isocalendar()
    return f"{year}-W{week:02d}"


def compute_objective_progress(
    *,
    objective_type: ObjectiveType | str,
    target: int,
    snapshot: QuestEvaluationSnapshot,
    current_progress: int,
    cadence: QuestCadence | None = None,
) -> int:
    """Compute the next progress total for an objective."""
    if objective_type is ObjectiveType.COMPLETE_TRACKS:
        if cadence is None:
            return min(snapshot.tracks_completed_lifetime, target)
        if snapshot.newly_completed_track:
            return min(current_progress + 1, target)
        return min(current_progress, target)

    if objective_type is ObjectiveType.DISTINCT_ARTISTS:
        return min(snapshot.distinct_artists_in_period, target)

    if objective_type is ObjectiveType.DISTINCT_GENRES:
        return min(snapshot.distinct_genres_in_period, target)

    if objective_type is ObjectiveType.LISTENING_MINUTES:
        if snapshot.validated_listening_delta_ms > 0:
            added = snapshot.validated_listening_delta_ms // 60_000
            return min(current_progress + added, target)
        return min(current_progress, target)

    if objective_type is ObjectiveType.WEEKLY_FOCUS_MINUTES:
        if snapshot.validated_listening_delta_ms > 0:
            added = snapshot.validated_listening_delta_ms // 60_000
            return min(current_progress + added, target)
        return min(snapshot.weekly_focus_minutes, target)

    if objective_type is ObjectiveType.STREAK_DAYS:
        return min(snapshot.streak_days, target)

    if objective_type is ObjectiveType.LEVEL_REACHED:
        return min(snapshot.user_level, target)

    objective_label = getattr(objective_type, "value", objective_type)
    msg = f"Unsupported objective type '{objective_label}'"
    raise ValueError(msg)


def completion_percentage(progress: int, target: int) -> float:
    """Return a clamped completion percentage."""
    if target <= 0:
        return 0.0
    return round(min(progress / target, 1.0) * 100, 2)
