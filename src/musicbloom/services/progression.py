"""Listening progression business logic."""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from musicbloom.db.mappers.progression import (
    build_daily_streak,
    build_listening_event_record,
    build_progress_summary,
    build_statistics,
    map_award_from_transaction,
)
from musicbloom.db.models.listening_event import ListeningEvent
from musicbloom.db.models.track_listening_state import TrackListeningState
from musicbloom.db.models.user_progress import UserProgress
from musicbloom.models.progression import (
    DailyListeningStreak,
    ListeningEventRecord,
    ListeningEventType,
    ListeningStatistics,
    PointsAwardExplanation,
    ProgressSummary,
)
from musicbloom.progression.levels import compute_user_level
from musicbloom.progression.policy import PolicyAward, ProgressionPolicy
from musicbloom.repositories.listening_event import ListeningEventRepository
from musicbloom.repositories.melody_points_transaction import (
    MelodyPointsTransactionRepository,
)
from musicbloom.repositories.track_listening_state import TrackListeningStateRepository
from musicbloom.repositories.user_progress import UserProgressRepository
from musicbloom.services.catalog import CatalogService
from musicbloom.services.progression_errors import (
    InvalidListeningDurationError,
    InvalidListeningEventError,
    TrackNotFoundError,
)

if TYPE_CHECKING:
    from musicbloom.services.quest_achievement import QuestAchievementService


@dataclass(slots=True)
class _EventProcessingResult:
    awards: list[PointsAwardExplanation]
    validated_delta_ms: int = 0
    completion_awarded: bool = False


class ProgressionService:
    """Service layer for listening progression and rewards."""

    def __init__(
        self,
        *,
        user_id: int,
        catalog_service: CatalogService,
        listening_event_repository: ListeningEventRepository,
        track_state_repository: TrackListeningStateRepository,
        transaction_repository: MelodyPointsTransactionRepository,
        progress_repository: UserProgressRepository,
        quest_achievement_service: "QuestAchievementService | None" = None,
        policy: ProgressionPolicy | None = None,
    ) -> None:
        self._user_id = user_id
        self._catalog_service = catalog_service
        self._listening_events = listening_event_repository
        self._track_states = track_state_repository
        self._transactions = transaction_repository
        self._progress = progress_repository
        self._quest_service = quest_achievement_service
        self._policy = policy or ProgressionPolicy()

    def submit_listening_event(
        self,
        *,
        track_id: str,
        event_type: ListeningEventType,
        position_ms: int,
        idempotency_key: str,
        occurred_at: datetime | None = None,
    ) -> ListeningEventRecord:
        """Process a listening event and apply deterministic rewards."""
        existing = self._listening_events.get_by_idempotency_key(
            user_id=self._user_id,
            idempotency_key=idempotency_key,
        )
        if existing is not None:
            return self._build_duplicate_event_response(existing)

        track = self._catalog_service.get_track(track_id)
        if track is None:
            raise TrackNotFoundError(f"Track '{track_id}' was not found")

        event_time = occurred_at or datetime.now(tz=UTC)
        if event_time.tzinfo is None:
            raise InvalidListeningEventError("occurred_at must be timezone-aware")

        try:
            self._policy.validate_position(
                position_ms=position_ms,
                track_duration_ms=track.duration_ms,
            )
        except ValueError as exc:
            raise InvalidListeningDurationError(str(exc)) from exc

        event = self._listening_events.add_event(
            user_id=self._user_id,
            track_id=track_id,
            event_type=event_type.value,
            idempotency_key=idempotency_key,
            position_ms=position_ms,
            occurred_at=event_time,
        )

        track_state = self._track_states.get_or_create(
            user_id=self._user_id,
            track_id=track_id,
        )
        progress = self._progress.require_for_user(self._user_id)

        result = self._process_event(
            event_type=event_type,
            position_ms=position_ms,
            track_duration_ms=track.duration_ms,
            track_state=track_state,
            progress=progress,
            event_id=event.id,
            track_id=track_id,
            occurred_at=event_time,
        )

        progress.level = compute_user_level(progress.experience_points).level

        if self._quest_service is not None:
            self._quest_service.evaluate_after_listening_event(
                track=track,
                event_type=event_type,
                occurred_at=event_time,
                validated_listening_delta_ms=result.validated_delta_ms,
                completion_awarded=result.completion_awarded,
            )

        return build_listening_event_record(
            event=event,
            awards=result.awards,
            melody_points_earned=sum(award.melody_points for award in result.awards),
            experience_earned=sum(award.experience for award in result.awards),
        )

    def get_progress_summary(self) -> ProgressSummary:
        """Return the current user's combined progression snapshot."""
        progress = self._progress.require_for_user(self._user_id)
        return build_progress_summary(
            progress=progress,
            tracks_completed=self._track_states.count_completed_for_user(self._user_id),
            total_listening_events=self._listening_events.count_for_user(self._user_id),
        )

    def get_statistics(self) -> ListeningStatistics:
        """Return aggregate listening statistics."""
        progress = self._progress.require_for_user(self._user_id)
        return build_statistics(
            progress=progress,
            tracks_completed=self._track_states.count_completed_for_user(self._user_id),
            total_listening_events=self._listening_events.count_for_user(self._user_id),
        )

    def get_streak(self) -> DailyListeningStreak:
        """Return the current daily listening streak."""
        progress = self._progress.require_for_user(self._user_id)
        return build_daily_streak(progress)

    def _build_duplicate_event_response(
        self,
        event: ListeningEvent,
    ) -> ListeningEventRecord:
        transactions = self._transactions.list_for_event(event.id)
        awards = [
            map_award_from_transaction(transaction)
            for transaction in transactions
        ]
        return build_listening_event_record(
            event=event,
            awards=awards,
            melody_points_earned=sum(award.melody_points for award in awards),
            experience_earned=sum(award.experience for award in awards),
            duplicate=True,
        )

    def _process_event(
        self,
        *,
        event_type: ListeningEventType,
        position_ms: int,
        track_duration_ms: int,
        track_state: TrackListeningState,
        progress: UserProgress,
        event_id: int,
        track_id: str,
        occurred_at: datetime,
    ) -> _EventProcessingResult:
        if event_type is ListeningEventType.STARTED:
            track_state.last_position_ms = max(
                track_state.last_position_ms,
                position_ms,
            )
            return _EventProcessingResult(awards=[])

        if event_type is ListeningEventType.SKIPPED:
            track_state.skipped = True
            track_state.last_position_ms = position_ms
            return _EventProcessingResult(awards=[])

        if event_type is ListeningEventType.PROGRESS:
            awards, validated_delta_ms = self._apply_progress_event(
                position_ms=position_ms,
                track_duration_ms=track_duration_ms,
                track_state=track_state,
                progress=progress,
                event_id=event_id,
                track_id=track_id,
                occurred_at=occurred_at,
            )
            return _EventProcessingResult(
                awards=awards,
                validated_delta_ms=validated_delta_ms,
            )

        if event_type is ListeningEventType.COMPLETED:
            if track_state.skipped:
                raise InvalidListeningEventError(
                    "Skipped tracks cannot be reported as completed",
                )
            track_state.last_position_ms = max(
                track_state.last_position_ms,
                position_ms,
            )
            completion_awards: list[PointsAwardExplanation] = []
            meaningful_listen = (
                track_state.validated_listening_ms
                >= self._policy.meaningful_listen_ms(track_duration_ms)
            )
            streak_award = self._maybe_apply_streak_bonus(
                progress=progress,
                occurred_at=occurred_at,
                meaningful_listen=meaningful_listen,
                event_id=event_id,
                track_id=track_id,
            )
            if streak_award is not None:
                completion_awards.append(streak_award)
            completion_awarded = False
            completion_award = self._policy.calculate_completion_award(
                position_ms=position_ms,
                track_duration_ms=track_duration_ms,
                skipped=track_state.skipped,
                completion_awarded=track_state.completion_awarded,
            )
            if completion_award is not None:
                track_state.completion_awarded = True
                completion_awarded = True
                completion_awards.append(
                    self._apply_award(
                        award=completion_award,
                        progress=progress,
                        event_id=event_id,
                        track_id=track_id,
                    ),
                )
            return _EventProcessingResult(
                awards=completion_awards,
                completion_awarded=completion_awarded,
            )

        raise InvalidListeningEventError(f"Unsupported event type '{event_type.value}'")

    def _apply_progress_event(
        self,
        *,
        position_ms: int,
        track_duration_ms: int,
        track_state: TrackListeningState,
        progress: UserProgress,
        event_id: int,
        track_id: str,
        occurred_at: datetime,
    ) -> tuple[list[PointsAwardExplanation], int]:
        if track_state.skipped:
            raise InvalidListeningEventError(
                "Skipped tracks cannot earn listening progress",
            )

        try:
            delta_ms = self._policy.validate_progress_delta(
                position_ms=position_ms,
                last_position_ms=track_state.last_position_ms,
                track_duration_ms=track_duration_ms,
            )
        except ValueError as exc:
            raise InvalidListeningDurationError(str(exc)) from exc

        track_state.last_position_ms = position_ms
        track_state.validated_listening_ms += delta_ms
        progress.total_listening_ms += delta_ms

        awards: list[PointsAwardExplanation] = []
        progress_award = self._policy.calculate_progress_award(
            validated_delta_ms=delta_ms,
            progress_points_awarded=track_state.progress_points_awarded,
            progress_experience_awarded=track_state.progress_experience_awarded,
        )
        if progress_award is not None:
            track_state.progress_points_awarded += progress_award.melody_points
            track_state.progress_experience_awarded += progress_award.experience
            awards.append(
                self._apply_award(
                    award=progress_award,
                    progress=progress,
                    event_id=event_id,
                    track_id=track_id,
                ),
            )

        meaningful_listen = (
            track_state.validated_listening_ms
            >= self._policy.meaningful_listen_ms(track_duration_ms)
        )
        streak_award = self._maybe_apply_streak_bonus(
            progress=progress,
            occurred_at=occurred_at,
            meaningful_listen=meaningful_listen,
            event_id=event_id,
            track_id=track_id,
        )
        if streak_award is not None:
            awards.append(streak_award)

        return awards, delta_ms

    def _maybe_apply_streak_bonus(
        self,
        *,
        progress: UserProgress,
        occurred_at: datetime,
        meaningful_listen: bool,
        event_id: int,
        track_id: str,
    ) -> PointsAwardExplanation | None:
        event_date = self._policy.utc_date_from_datetime(occurred_at)
        if progress.streak_bonus_utc_date != event_date:
            progress.streak_bonus_points_today = 0
            progress.streak_bonus_utc_date = event_date

        updated_days, updated_date = self._policy.update_streak(
            current_days=progress.streak_current_days,
            last_listening_utc_date=progress.streak_last_utc_date,
            event_utc_date=event_date,
            meaningful_listen=meaningful_listen,
        )
        progress.streak_current_days = updated_days
        progress.streak_last_utc_date = updated_date

        streak_award = self._policy.calculate_streak_bonus(
            streak_days=progress.streak_current_days,
            bonus_awarded_today=progress.streak_bonus_points_today,
        )
        if streak_award is None or not meaningful_listen:
            return None

        progress.streak_bonus_points_today += streak_award.melody_points
        return self._apply_award(
            award=streak_award,
            progress=progress,
            event_id=event_id,
            track_id=track_id,
        )

    def _apply_award(
        self,
        *,
        award: PolicyAward,
        progress: UserProgress,
        event_id: int,
        track_id: str,
    ) -> PointsAwardExplanation:
        progress.melody_points += award.melody_points
        progress.experience_points += award.experience
        self._transactions.add_transaction(
            user_id=self._user_id,
            amount=award.melody_points,
            experience_amount=award.experience,
            reason=award.reason.value,
            explanation=award.explanation,
            track_id=track_id,
            listening_event_id=event_id,
        )
        return PointsAwardExplanation(
            reason=award.reason,
            melody_points=award.melody_points,
            experience=award.experience,
            explanation=award.explanation,
        )
