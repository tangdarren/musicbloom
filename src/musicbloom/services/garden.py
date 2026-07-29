"""Garden business logic."""

from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from musicbloom.db.mappers.progression import build_daily_streak
from musicbloom.db.mappers.rewards import (
    build_achievement_progress_view,
    build_decoration_unlock,
)
from musicbloom.db.models.garden_profile import GardenProfile
from musicbloom.db.models.user_progress import UserProgress
from musicbloom.models.garden import (
    ArtistFlower,
    DecorationCatalogEntry,
    EquipDecorationResult,
    EquippedDecorationView,
    GardenMood,
    GardenProfileView,
    GardenState,
    ListeningMilestonePlant,
    RecentAchievement,
)
from musicbloom.models.rewards import DecorationUnlock, ProgressStatus
from musicbloom.progression.levels import compute_user_level
from musicbloom.repositories.achievement_progress import AchievementProgressRepository
from musicbloom.repositories.decoration_unlock import DecorationUnlockRepository
from musicbloom.repositories.demo_rewards_catalog import DemoRewardsCatalogRepository
from musicbloom.repositories.equipped_decoration import EquippedDecorationRepository
from musicbloom.repositories.garden_profile import GardenProfileRepository
from musicbloom.repositories.track_listening_state import TrackListeningStateRepository
from musicbloom.repositories.user_progress import UserProgressRepository
from musicbloom.services.catalog import CatalogService
from musicbloom.services.garden_errors import (
    DecorationLockedError,
    DecorationNotEquippedError,
    DecorationNotFoundError,
    GardenProfileNotFoundError,
)


@dataclass(frozen=True, slots=True)
class _MilestoneDefinition:
    id: str
    title: str
    description: str
    target: int
    progress_for: Callable[[UserProgress, int], int]


MILESTONE_DEFINITIONS: tuple[_MilestoneDefinition, ...] = (
    _MilestoneDefinition(
        id="milestone-first-track",
        title="First Sprout",
        description="Complete your first track",
        target=1,
        progress_for=lambda _progress, tracks_completed: tracks_completed,
    ),
    _MilestoneDefinition(
        id="milestone-three-tracks",
        title="Triple Bloom",
        description="Complete three tracks",
        target=3,
        progress_for=lambda _progress, tracks_completed: tracks_completed,
    ),
    _MilestoneDefinition(
        id="milestone-thirty-minutes",
        title="Deep Listening",
        description="Listen for thirty minutes",
        target=30,
        progress_for=lambda progress, _tracks_completed: progress.total_listening_ms
        // 60_000,
    ),
    _MilestoneDefinition(
        id="milestone-streak-three",
        title="Steady Flame",
        description="Maintain a three-day streak",
        target=3,
        progress_for=lambda progress, _tracks_completed: progress.streak_current_days,
    ),
    _MilestoneDefinition(
        id="milestone-level-two",
        title="Level Bloom",
        description="Reach level two",
        target=2,
        progress_for=lambda progress, _tracks_completed: progress.level,
    ),
)

STREAK_MILESTONE_DAYS = (3, 7)


class GardenService:
    """Service layer for garden state and decoration management."""

    RECENT_ACHIEVEMENT_LIMIT = 5

    def __init__(
        self,
        *,
        user_id: int,
        catalog_service: CatalogService,
        rewards_catalog: DemoRewardsCatalogRepository,
        garden_profile_repository: GardenProfileRepository,
        equipped_decoration_repository: EquippedDecorationRepository,
        decoration_unlock_repository: DecorationUnlockRepository,
        user_progress_repository: UserProgressRepository,
        track_state_repository: TrackListeningStateRepository,
        achievement_progress_repository: AchievementProgressRepository,
    ) -> None:
        self._user_id = user_id
        self._catalog_service = catalog_service
        self._rewards_catalog = rewards_catalog
        self._garden_profiles = garden_profile_repository
        self._equipped = equipped_decoration_repository
        self._decoration_unlocks = decoration_unlock_repository
        self._user_progress = user_progress_repository
        self._track_states = track_state_repository
        self._achievement_progress = achievement_progress_repository

    def get_garden_state(self) -> GardenState:
        """Return the current user's aggregated garden state."""
        profile = self._require_garden_profile()
        progress = self._user_progress.require_for_user(self._user_id)
        tracks_completed = self._track_states.count_completed_for_user(self._user_id)
        level = compute_user_level(progress.experience_points)

        unlocked = self._build_unlocked_decorations()
        equipped = self._build_equipped_decorations()

        return GardenState(
            profile=GardenProfileView(
                garden_name=profile.garden_name,
                theme=profile.theme,
            ),
            mood=self._derive_mood(progress, tracks_completed),
            level=level,
            melody_points=progress.melody_points,
            streak=build_daily_streak(progress),
            artist_flowers=self._build_artist_flowers(),
            milestone_plants=self._build_milestone_plants(
                progress,
                tracks_completed,
            ),
            unlocked_decorations=unlocked,
            equipped_decorations=equipped,
            recent_achievements=self._build_recent_achievements(progress.level),
            tracks_completed=tracks_completed,
            total_listening_minutes=progress.total_listening_ms // 60_000,
        )

    def list_decorations(self) -> list[DecorationCatalogEntry]:
        """Return the full decoration catalog with unlock and equip status."""
        unlocked_ids = {
            record.decoration_id
            for record in self._decoration_unlocks.list_for_user(self._user_id)
        }
        equipped_ids = {
            record.decoration_id
            for record in self._equipped.list_for_user(self._user_id)
        }

        entries: list[DecorationCatalogEntry] = []
        for decoration in self._rewards_catalog.list_decorations():
            entries.append(
                DecorationCatalogEntry(
                    decoration=decoration,
                    unlocked=decoration.id in unlocked_ids,
                    equipped=decoration.id in equipped_ids,
                ),
            )
        return entries

    def equip_decoration(self, decoration_id: str) -> EquipDecorationResult:
        """Equip an unlocked decoration in its default slot."""
        decoration = self._rewards_catalog.get_decoration(decoration_id)
        if decoration is None:
            raise DecorationNotFoundError(
                f"Decoration '{decoration_id}' was not found",
            )

        unlock = self._decoration_unlocks.get_for_user_and_decoration(
            self._user_id,
            decoration_id,
        )
        if unlock is None:
            raise DecorationLockedError(
                "Decoration is locked and cannot be equipped",
            )

        record = self._equipped.equip(
            user_id=self._user_id,
            decoration_id=decoration_id,
            slot=decoration.slot,
        )
        return EquipDecorationResult(
            decoration=decoration,
            slot=record.slot,
            equipped_at=record.equipped_at,
        )

    def unequip_decoration(self, decoration_id: str) -> None:
        """Remove an equipped decoration from the garden."""
        decoration = self._rewards_catalog.get_decoration(decoration_id)
        if decoration is None:
            raise DecorationNotFoundError(
                f"Decoration '{decoration_id}' was not found",
            )

        removed = self._equipped.unequip(
            user_id=self._user_id,
            decoration_id=decoration_id,
        )
        if not removed:
            raise DecorationNotEquippedError(
                "Decoration is not currently equipped",
            )

    def streak_milestone_days(self) -> tuple[int, ...]:
        """Return streak day thresholds that trigger garden effects."""
        return STREAK_MILESTONE_DAYS

    def _require_garden_profile(self) -> GardenProfile:
        profile = self._garden_profiles.get_for_user(self._user_id)
        if profile is None:
            raise GardenProfileNotFoundError("Garden profile was not found")
        return profile

    def _derive_mood(
        self,
        progress: UserProgress,
        tracks_completed: int,
    ) -> GardenMood:
        if progress.streak_current_days >= 3 or progress.level >= 2:
            return GardenMood.BLOOMING
        if tracks_completed >= 1 or progress.total_listening_ms >= 60_000:
            return GardenMood.CHEERFUL
        return GardenMood.SERENE

    def _build_artist_flowers(self) -> list[ArtistFlower]:
        artist_counts: Counter[str] = Counter()
        artist_names: dict[str, str] = {}
        for track_id in self._track_states.list_completed_track_ids_for_user(
            self._user_id,
        ):
            track = self._catalog_service.get_track(track_id)
            if track is None:
                continue
            artist_counts[track.artist_id] += 1
            artist_names[track.artist_id] = track.artist_name

        flowers: list[ArtistFlower] = []
        for artist_id, completions in artist_counts.most_common(6):
            artist_name = artist_names.get(artist_id)
            if artist_name is None:
                continue
            flowers.append(
                ArtistFlower(
                    artist_id=artist_id,
                    artist_name=artist_name,
                    completions=completions,
                    bloom_stage=min(completions, 3),
                ),
            )
        return flowers

    def _build_milestone_plants(
        self,
        progress: UserProgress,
        tracks_completed: int,
    ) -> list[ListeningMilestonePlant]:
        plants: list[ListeningMilestonePlant] = []
        for milestone in MILESTONE_DEFINITIONS:
            current = milestone.progress_for(progress, tracks_completed)
            plants.append(
                ListeningMilestonePlant(
                    id=milestone.id,
                    title=milestone.title,
                    description=milestone.description,
                    target=milestone.target,
                    progress=min(current, milestone.target),
                    unlocked=current >= milestone.target,
                ),
            )
        return plants

    def _build_unlocked_decorations(self) -> list[DecorationUnlock]:
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
        return unlocked

    def _build_equipped_decorations(self) -> list[EquippedDecorationView]:
        equipped: list[EquippedDecorationView] = []
        for record in self._equipped.list_for_user(self._user_id):
            decoration = self._rewards_catalog.get_decoration(record.decoration_id)
            if decoration is not None:
                equipped.append(
                    EquippedDecorationView(
                        decoration=decoration,
                        slot=record.slot,
                        equipped_at=record.equipped_at,
                    ),
                )
        return equipped

    def _build_recent_achievements(self, user_level: int) -> list[RecentAchievement]:
        achievements: list[tuple[datetime | None, RecentAchievement]] = []
        for achievement in self._rewards_catalog.list_achievements():
            reward = self._rewards_catalog.get_reward(achievement.reward_id)
            if reward is None:
                continue
            record = self._achievement_progress.ensure_progress(
                user_id=self._user_id,
                achievement_id=achievement.id,
            )
            view = build_achievement_progress_view(
                achievement=achievement,
                reward=reward,
                record=record,
                user_level=user_level,
            )
            if view.status is ProgressStatus.LOCKED:
                continue
            achievements.append(
                (
                    view.completed_at,
                    RecentAchievement(
                        achievement_id=achievement.id,
                        title=achievement.title,
                        status=view.status,
                        completed_at=view.completed_at,
                    ),
                ),
            )

        achievements.sort(
            key=lambda item: item[0].timestamp() if item[0] is not None else 0,
            reverse=True,
        )
        return [item[1] for item in achievements[: self.RECENT_ACHIEVEMENT_LIMIT]]
