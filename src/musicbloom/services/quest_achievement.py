"""Quest and achievement business logic."""

from collections.abc import Callable
from datetime import UTC, datetime, time, timedelta

from musicbloom.db.mappers.rewards import (
    build_achievement_progress_view,
    build_decoration_unlock,
    build_quest_progress_view,
    build_reward_claim_record,
)
from musicbloom.models.catalog import Track
from musicbloom.models.progression import ListeningEventType
from musicbloom.models.rewards import (
    AchievementProgressView,
    ProgressStatus,
    QuestProgressView,
    Reward,
    RewardClaimResult,
    RewardsInventory,
    RewardType,
)
from musicbloom.repositories.achievement_progress import AchievementProgressRepository
from musicbloom.repositories.decoration_unlock import DecorationUnlockRepository
from musicbloom.repositories.demo_rewards_catalog import DemoRewardsCatalogRepository
from musicbloom.repositories.listening_event import ListeningEventRepository
from musicbloom.repositories.quest_progress import QuestProgressRepository
from musicbloom.repositories.reward_claim import RewardClaimRepository
from musicbloom.repositories.track_listening_state import TrackListeningStateRepository
from musicbloom.repositories.user_progress import UserProgressRepository
from musicbloom.rewards.evaluator import (
    QuestEvaluationSnapshot,
    compute_objective_progress,
    period_key_for_cadence,
)
from musicbloom.services.catalog import CatalogService
from musicbloom.services.quest_errors import (
    AchievementNotFoundError,
    QuestNotFoundError,
    RewardAlreadyClaimedError,
    RewardNotClaimableError,
    RewardNotFoundError,
)


def _period_bounds(
    cadence_moment: datetime,
    *,
    weekly: bool,
) -> tuple[datetime, datetime]:
    utc_moment = cadence_moment.astimezone(UTC)
    if weekly:
        start_date = utc_moment.date() - timedelta(days=utc_moment.weekday())
    else:
        start_date = utc_moment.date()
    start = datetime.combine(start_date, time.min, tzinfo=UTC)
    return start, utc_moment


class QuestAchievementService:
    """Service layer for quests, achievements, and reward claims."""

    SOURCE_QUEST = "quest"
    SOURCE_ACHIEVEMENT = "achievement"

    def __init__(
        self,
        *,
        user_id: int,
        catalog_service: CatalogService,
        rewards_catalog: DemoRewardsCatalogRepository,
        quest_progress_repository: QuestProgressRepository,
        achievement_progress_repository: AchievementProgressRepository,
        reward_claim_repository: RewardClaimRepository,
        decoration_unlock_repository: DecorationUnlockRepository,
        listening_event_repository: ListeningEventRepository,
        track_state_repository: TrackListeningStateRepository,
        user_progress_repository: UserProgressRepository,
    ) -> None:
        self._user_id = user_id
        self._catalog_service = catalog_service
        self._rewards_catalog = rewards_catalog
        self._quest_progress = quest_progress_repository
        self._achievement_progress = achievement_progress_repository
        self._reward_claims = reward_claim_repository
        self._decoration_unlocks = decoration_unlock_repository
        self._listening_events = listening_event_repository
        self._track_states = track_state_repository
        self._user_progress = user_progress_repository

    def seed_progress_records(self) -> None:
        """Ensure demo quest and achievement progress rows exist."""
        for quest in self._rewards_catalog.list_quests():
            period_key = period_key_for_cadence(
                quest.cadence,
                datetime.now(tz=UTC),
            )
            self._quest_progress.ensure_progress(
                user_id=self._user_id,
                quest_id=quest.id,
                period_key=period_key,
            )
        for achievement in self._rewards_catalog.list_achievements():
            self._achievement_progress.ensure_progress(
                user_id=self._user_id,
                achievement_id=achievement.id,
            )

    def list_quests(self) -> list[QuestProgressView]:
        """Return all quests with current progress."""
        user_level = self._user_progress.require_for_user(self._user_id).level
        views: list[QuestProgressView] = []
        for quest in self._rewards_catalog.list_quests():
            reward = self._require_reward(quest.reward_id)
            period_key = period_key_for_cadence(
                quest.cadence,
                datetime.now(tz=UTC),
            )
            record = self._quest_progress.ensure_progress(
                user_id=self._user_id,
                quest_id=quest.id,
                period_key=period_key,
            )
            views.append(
                build_quest_progress_view(
                    quest=quest,
                    reward=reward,
                    record=record,
                    user_level=user_level,
                ),
            )
        return views

    def list_achievements(self) -> list[AchievementProgressView]:
        """Return all achievements with current progress."""
        user_level = self._user_progress.require_for_user(self._user_id).level
        views: list[AchievementProgressView] = []
        for achievement in self._rewards_catalog.list_achievements():
            reward = self._require_reward(achievement.reward_id)
            record = self._achievement_progress.ensure_progress(
                user_id=self._user_id,
                achievement_id=achievement.id,
            )
            views.append(
                build_achievement_progress_view(
                    achievement=achievement,
                    reward=reward,
                    record=record,
                    user_level=user_level,
                ),
            )
        return views

    def claim_quest(self, quest_id: str) -> RewardClaimResult:
        """Claim a completed quest reward."""
        quest = self._rewards_catalog.get_quest(quest_id)
        if quest is None:
            raise QuestNotFoundError(f"Quest '{quest_id}' was not found")
        reward = self._require_reward(quest.reward_id)
        period_key = period_key_for_cadence(quest.cadence, datetime.now(tz=UTC))
        record = self._quest_progress.ensure_progress(
            user_id=self._user_id,
            quest_id=quest.id,
            period_key=period_key,
        )
        return self._claim_reward(
            source_type=self.SOURCE_QUEST,
            source_id=quest.id,
            reward=reward,
            status=build_quest_progress_view(
                quest=quest,
                reward=reward,
                record=record,
                user_level=self._user_progress.require_for_user(self._user_id).level,
            ).status,
            on_claimed=lambda: self._quest_progress.mark_claimed(record),
        )

    def claim_achievement(self, achievement_id: str) -> RewardClaimResult:
        """Claim a completed achievement reward."""
        achievement = self._rewards_catalog.get_achievement(achievement_id)
        if achievement is None:
            raise AchievementNotFoundError(
                f"Achievement '{achievement_id}' was not found",
            )
        reward = self._require_reward(achievement.reward_id)
        record = self._achievement_progress.ensure_progress(
            user_id=self._user_id,
            achievement_id=achievement.id,
        )
        return self._claim_reward(
            source_type=self.SOURCE_ACHIEVEMENT,
            source_id=achievement.id,
            reward=reward,
            status=build_achievement_progress_view(
                achievement=achievement,
                reward=reward,
                record=record,
                user_level=self._user_progress.require_for_user(self._user_id).level,
            ).status,
            on_claimed=lambda: self._achievement_progress.mark_claimed(record),
        )

    def get_rewards_inventory(self) -> RewardsInventory:
        """Return reward inventory and claim history."""
        progress = self._user_progress.require_for_user(self._user_id)
        unlocked = []
        for record in self._decoration_unlocks.list_for_user(self._user_id):
            decoration = self._rewards_catalog.get_decoration(record.decoration_id)
            if decoration is not None:
                unlocked.append(
                    build_decoration_unlock(
                        decoration=decoration,
                        record=record,
                    ),
                )
        history = [
            build_reward_claim_record(claim=claim, catalog=self._rewards_catalog)
            for claim in self._reward_claims.list_for_user(self._user_id)
        ]
        return RewardsInventory(
            melody_points=progress.melody_points,
            unlocked_decorations=unlocked,
            claim_history=history,
        )

    def evaluate_after_listening_event(
        self,
        *,
        track: Track,
        event_type: ListeningEventType,
        occurred_at: datetime,
        validated_listening_delta_ms: int,
        completion_awarded: bool,
    ) -> None:
        """Update quest and achievement progress from a validated listening event."""
        snapshot = self._build_snapshot(
            track=track,
            event_type=event_type,
            occurred_at=occurred_at,
            validated_listening_delta_ms=validated_listening_delta_ms,
            completion_awarded=completion_awarded,
        )
        user_level = self._user_progress.require_for_user(self._user_id).level

        for quest in self._rewards_catalog.list_quests():
            if user_level < quest.unlock_level:
                continue
            period_key = period_key_for_cadence(quest.cadence, occurred_at)
            record = self._quest_progress.ensure_progress(
                user_id=self._user_id,
                quest_id=quest.id,
                period_key=period_key,
            )
            if record.claimed_at is not None:
                continue
            progress_value = compute_objective_progress(
                objective_type=quest.objective_type,
                target=quest.target,
                snapshot=snapshot,
                current_progress=record.progress,
                cadence=quest.cadence,
            )
            completed = progress_value >= quest.target
            status = "completed" if completed else "active"
            self._quest_progress.save_progress(
                record=record,
                status=status,
                progress=progress_value,
                completed=completed,
            )

        for achievement in self._rewards_catalog.list_achievements():
            if user_level < achievement.unlock_level:
                continue
            achievement_record = self._achievement_progress.ensure_progress(
                user_id=self._user_id,
                achievement_id=achievement.id,
            )
            if achievement_record.claimed_at is not None:
                continue
            progress_value = compute_objective_progress(
                objective_type=achievement.objective_type,
                target=achievement.target,
                snapshot=snapshot,
                current_progress=achievement_record.progress,
                cadence=None,
            )
            completed = progress_value >= achievement.target
            self._achievement_progress.save_progress(
                record=achievement_record,
                progress=progress_value,
                completed=completed,
            )

    def _build_snapshot(
        self,
        *,
        track: Track,
        event_type: ListeningEventType,
        occurred_at: datetime,
        validated_listening_delta_ms: int,
        completion_awarded: bool,
    ) -> QuestEvaluationSnapshot:
        progress = self._user_progress.require_for_user(self._user_id)
        daily_start, daily_end = _period_bounds(occurred_at, weekly=False)
        weekly_start, weekly_end = _period_bounds(occurred_at, weekly=True)

        daily_completed = self._listening_events.list_completed_track_ids_in_period(
            user_id=self._user_id,
            start=daily_start,
            end=daily_end,
        )
        weekly_completed = self._listening_events.list_completed_track_ids_in_period(
            user_id=self._user_id,
            start=weekly_start,
            end=weekly_end,
        )

        return QuestEvaluationSnapshot(
            user_level=progress.level,
            total_listening_ms=progress.total_listening_ms,
            streak_days=progress.streak_current_days,
            tracks_completed_lifetime=self._track_states.count_completed_for_user(
                self._user_id,
            ),
            distinct_artists_in_period=self._count_distinct_artists(daily_completed),
            distinct_genres_in_period=self._count_distinct_genres(weekly_completed),
            weekly_focus_minutes=0,
            newly_completed_track=(
                event_type is ListeningEventType.COMPLETED and completion_awarded
            ),
            validated_listening_delta_ms=validated_listening_delta_ms,
        )

    def _count_distinct_artists(self, track_ids: list[str]) -> int:
        artists: set[str] = set()
        for track_id in track_ids:
            track = self._catalog_service.get_track(track_id)
            if track is not None:
                artists.add(track.artist_id)
        return len(artists)

    def _count_distinct_genres(self, track_ids: list[str]) -> int:
        genres: set[str] = set()
        for track_id in track_ids:
            track = self._catalog_service.get_track(track_id)
            if track is not None:
                genres.add(track.genre)
        return len(genres)

    def _claim_reward(
        self,
        *,
        source_type: str,
        source_id: str,
        reward: Reward,
        status: ProgressStatus,
        on_claimed: Callable[[], object],
    ) -> RewardClaimResult:
        if status is ProgressStatus.LOCKED:
            raise RewardNotClaimableError("Reward is locked")
        if status is ProgressStatus.CLAIMED:
            raise RewardAlreadyClaimedError("Reward has already been claimed")
        if status is not ProgressStatus.COMPLETED:
            raise RewardNotClaimableError("Reward is not complete yet")

        existing = self._reward_claims.get_for_source(
            user_id=self._user_id,
            source_type=source_type,
            source_id=source_id,
        )
        if existing is not None:
            raise RewardAlreadyClaimedError("Reward has already been claimed")

        user_progress = self._user_progress.require_for_user(self._user_id)
        decoration = None
        melody_points_granted = 0

        if reward.reward_type is RewardType.MELODY_POINTS:
            melody_points_granted = reward.melody_points
            user_progress.melody_points += melody_points_granted
        elif reward.reward_type is RewardType.DECORATION_UNLOCK:
            if reward.decoration_id is None:
                msg = "Decoration reward is missing decoration_id"
                raise RewardNotFoundError(msg)
            self._decoration_unlocks.unlock(
                user_id=self._user_id,
                decoration_id=reward.decoration_id,
            )
            decoration = self._rewards_catalog.get_decoration(reward.decoration_id)
            if decoration is None:
                raise RewardNotFoundError(
                    f"Decoration '{reward.decoration_id}' was not found",
                )

        claim = self._reward_claims.add_claim(
            user_id=self._user_id,
            reward_id=reward.id,
            source_type=source_type,
            source_id=source_id,
            melody_points_granted=melody_points_granted,
            decoration_id=reward.decoration_id,
        )
        on_claimed()

        return RewardClaimResult(
            source_type=source_type,
            source_id=source_id,
            reward=reward,
            melody_points_granted=melody_points_granted,
            decoration_unlocked=decoration,
            claimed_at=claim.claimed_at,
        )

    def _require_reward(self, reward_id: str) -> Reward:
        reward = self._rewards_catalog.get_reward(reward_id)
        if reward is None:
            raise RewardNotFoundError(f"Reward '{reward_id}' was not found")
        return reward
