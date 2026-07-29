"""Deterministic scoring rules for listening progression."""

from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta

from musicbloom.models.progression import PointsAwardReason


@dataclass(frozen=True, slots=True)
class PolicyAward:
    """Award computed by progression policy rules."""

    melody_points: int
    experience: int
    reason: PointsAwardReason
    explanation: str


class ProgressionPolicy:
    """Transparent, deterministic listening progression rules."""

    COMPLETION_THRESHOLD_RATIO = 0.90
    MEANINGFUL_LISTEN_THRESHOLD_RATIO = 0.30
    PROGRESS_INTERVAL_MS = 30_000
    PROGRESS_POINTS_PER_INTERVAL = 2
    PROGRESS_EXPERIENCE_PER_INTERVAL = 3
    MAX_PROGRESS_POINTS_PER_TRACK = 20
    MAX_PROGRESS_EXPERIENCE_PER_TRACK = 30
    COMPLETION_BONUS_POINTS = 15
    COMPLETION_EXPERIENCE = 25
    STREAK_BONUS_POINTS = 10
    MAX_DAILY_STREAK_BONUS = 50
    MAX_POSITION_JUMP_MS = 60_000

    def validate_position(self, *, position_ms: int, track_duration_ms: int) -> None:
        """Ensure playback position is within track bounds."""
        if position_ms < 0:
            msg = "Playback position cannot be negative"
            raise ValueError(msg)
        if position_ms > track_duration_ms:
            msg = "Playback position exceeds track duration"
            raise ValueError(msg)

    def validate_progress_delta(
        self,
        *,
        position_ms: int,
        last_position_ms: int,
        track_duration_ms: int,
    ) -> int:
        """Return validated listening delta for a progress event."""
        self.validate_position(
            position_ms=position_ms,
            track_duration_ms=track_duration_ms,
        )
        if position_ms < last_position_ms:
            msg = "Playback position cannot move backward for progress events"
            raise ValueError(msg)

        delta_ms = position_ms - last_position_ms
        if delta_ms > self.MAX_POSITION_JUMP_MS:
            msg = "Playback progress jump exceeds allowed threshold"
            raise ValueError(msg)
        return delta_ms

    def meaningful_listen_ms(self, track_duration_ms: int) -> int:
        """Return the listening threshold that counts toward streaks."""
        return int(track_duration_ms * self.MEANINGFUL_LISTEN_THRESHOLD_RATIO)

    def completion_threshold_ms(self, track_duration_ms: int) -> int:
        """Return the position required to qualify for completion."""
        return int(track_duration_ms * self.COMPLETION_THRESHOLD_RATIO)

    def calculate_progress_award(
        self,
        *,
        validated_delta_ms: int,
        progress_points_awarded: int,
        progress_experience_awarded: int,
    ) -> PolicyAward | None:
        """Award Melody Points for validated listening progress."""
        if validated_delta_ms < self.PROGRESS_INTERVAL_MS:
            return None

        intervals = validated_delta_ms // self.PROGRESS_INTERVAL_MS
        points = intervals * self.PROGRESS_POINTS_PER_INTERVAL
        experience = intervals * self.PROGRESS_EXPERIENCE_PER_INTERVAL

        remaining_points = self.MAX_PROGRESS_POINTS_PER_TRACK - progress_points_awarded
        remaining_experience = (
            self.MAX_PROGRESS_EXPERIENCE_PER_TRACK - progress_experience_awarded
        )
        if remaining_points <= 0 and remaining_experience <= 0:
            return None

        points = min(points, max(remaining_points, 0))
        experience = min(experience, max(remaining_experience, 0))

        return PolicyAward(
            melody_points=points,
            experience=experience,
            reason=PointsAwardReason.LISTENING_PROGRESS,
            explanation=(
                f"Awarded {points} Melody Points and {experience} experience for "
                f"{intervals} validated progress interval(s)."
            ),
        )

    def calculate_completion_award(
        self,
        *,
        position_ms: int,
        track_duration_ms: int,
        skipped: bool,
        completion_awarded: bool,
    ) -> PolicyAward | None:
        """Award completion bonus when a track is finished without skipping."""
        if skipped:
            return None
        if completion_awarded:
            return None
        if position_ms < self.completion_threshold_ms(track_duration_ms):
            return None

        return PolicyAward(
            melody_points=self.COMPLETION_BONUS_POINTS,
            experience=self.COMPLETION_EXPERIENCE,
            reason=PointsAwardReason.TRACK_COMPLETION,
            explanation=(
                f"Awarded {self.COMPLETION_BONUS_POINTS} Melody Points and "
                f"{self.COMPLETION_EXPERIENCE} experience for completing the track."
            ),
        )

    def calculate_streak_bonus(
        self,
        *,
        streak_days: int,
        bonus_awarded_today: int,
    ) -> PolicyAward | None:
        """Award capped daily streak bonus Melody Points."""
        if streak_days <= 0:
            return None

        remaining_cap = self.MAX_DAILY_STREAK_BONUS - bonus_awarded_today
        if remaining_cap <= 0:
            return None

        points = min(self.STREAK_BONUS_POINTS, remaining_cap)
        return PolicyAward(
            melody_points=points,
            experience=0,
            reason=PointsAwardReason.DAILY_STREAK,
            explanation=(
                f"Awarded {points} Melody Points for a "
                f"{streak_days}-day listening streak."
            ),
        )

    def update_streak(
        self,
        *,
        current_days: int,
        last_listening_utc_date: date | None,
        event_utc_date: date,
        meaningful_listen: bool,
    ) -> tuple[int, date | None]:
        """Update streak counters using UTC calendar dates."""
        if not meaningful_listen:
            return current_days, last_listening_utc_date

        if last_listening_utc_date == event_utc_date:
            return current_days, last_listening_utc_date

        if (
            last_listening_utc_date is not None
            and last_listening_utc_date == event_utc_date - timedelta(days=1)
        ):
            return current_days + 1, event_utc_date

        return 1, event_utc_date

    @staticmethod
    def utc_date_from_datetime(value: datetime) -> date:
        """Normalize an aware datetime to a UTC calendar date."""
        if value.tzinfo is None:
            msg = "Datetime must be timezone-aware"
            raise ValueError(msg)
        return value.astimezone(UTC).date()
