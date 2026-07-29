"""Additional quest and achievement coverage tests."""

from datetime import UTC, datetime

import pytest
from sqlalchemy.orm import Session

from musicbloom.db.init import get_demo_user
from musicbloom.db.mappers.rewards import (
    build_decoration_unlock,
    derive_achievement_status,
    derive_quest_status,
)
from musicbloom.db.models.achievement_progress import AchievementProgress
from musicbloom.db.models.decoration_unlock import DecorationUnlockRecord
from musicbloom.db.models.quest_progress import QuestProgress
from musicbloom.models.progression import ListeningEventType
from musicbloom.models.rewards import ProgressStatus, QuestCadence, Reward, RewardType
from musicbloom.repositories.achievement_progress import AchievementProgressRepository
from musicbloom.repositories.decoration_unlock import DecorationUnlockRepository
from musicbloom.repositories.demo_catalog import DemoCatalogRepository
from musicbloom.repositories.demo_rewards_catalog import DemoRewardsCatalogRepository
from musicbloom.repositories.demo_rewards_data import DEMO_ACHIEVEMENTS, DEMO_QUESTS
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
from musicbloom.services.quest_achievement import QuestAchievementService
from musicbloom.services.quest_errors import (
    RewardAlreadyClaimedError,
    RewardNotClaimableError,
    RewardNotFoundError,
)


@pytest.fixture
def quest_service(db_session: Session) -> QuestAchievementService:
    user = get_demo_user(db_session)
    return QuestAchievementService(
        user_id=user.id,
        catalog_service=CatalogService(DemoCatalogRepository()),
        rewards_catalog=DemoRewardsCatalogRepository(),
        quest_progress_repository=QuestProgressRepository(db_session),
        achievement_progress_repository=AchievementProgressRepository(db_session),
        reward_claim_repository=RewardClaimRepository(db_session),
        decoration_unlock_repository=DecorationUnlockRepository(db_session),
        listening_event_repository=ListeningEventRepository(db_session),
        track_state_repository=TrackListeningStateRepository(db_session),
        user_progress_repository=UserProgressRepository(db_session),
    )


def test_derive_locked_and_claimed_statuses() -> None:
    quest = DEMO_QUESTS[0]
    locked_record = QuestProgress(
        id=1,
        user_id=1,
        quest_id=quest.id,
        status="active",
        progress=0,
        period_key="2026-01-01",
    )
    claimed_record = QuestProgress(
        id=2,
        user_id=1,
        quest_id=quest.id,
        status="claimed",
        progress=3,
        period_key="2026-01-01",
        claimed_at=datetime.now(tz=UTC),
    )

    assert (
        derive_quest_status(quest=quest, record=locked_record, user_level=0)
        is ProgressStatus.LOCKED
    )
    assert (
        derive_quest_status(quest=quest, record=claimed_record, user_level=1)
        is ProgressStatus.CLAIMED
    )
    assert (
        derive_quest_status(
            quest=quest,
            record=QuestProgress(
                id=3,
                user_id=1,
                quest_id=quest.id,
                status="completed",
                progress=3,
                period_key="2026-01-01",
                completed_at=datetime.now(tz=UTC),
            ),
            user_level=1,
        )
        is ProgressStatus.COMPLETED
    )
    assert (
        derive_achievement_status(
            achievement=DEMO_ACHIEVEMENTS[0],
            record=AchievementProgress(
                id=1,
                user_id=1,
                achievement_id=DEMO_ACHIEVEMENTS[0].id,
                progress=2,
                completed_at=datetime.now(tz=UTC),
            ),
            user_level=1,
        )
        is ProgressStatus.COMPLETED
    )
    assert (
        derive_quest_status(
            quest=quest,
            record=QuestProgress(
                id=4,
                user_id=1,
                quest_id=quest.id,
                status="active",
                progress=0,
                period_key="2026-01-01",
            ),
            user_level=1,
        )
        is ProgressStatus.ACTIVE
    )


def test_build_decoration_unlock_mapper() -> None:
    decoration = DemoRewardsCatalogRepository().get_decoration("decoration-lantern-001")
    assert decoration is not None
    unlock = build_decoration_unlock(
        decoration=decoration,
        record=DecorationUnlockRecord(
            id=1,
            user_id=1,
            decoration_id=decoration.id,
            unlocked_at=datetime.now(tz=UTC),
        ),
    )

    assert unlock.decoration.id == decoration.id


def test_evaluator_unsupported_objective_raises() -> None:
    snapshot = QuestEvaluationSnapshot(
        user_level=1,
        total_listening_ms=0,
        streak_days=0,
        tracks_completed_lifetime=0,
        distinct_artists_in_period=0,
        distinct_genres_in_period=0,
        weekly_focus_minutes=0,
    )

    with pytest.raises(ValueError, match="Unsupported objective type"):
        compute_objective_progress(
            objective_type="unknown",  # type: ignore[arg-type]
            target=1,
            snapshot=snapshot,
            current_progress=0,
            cadence=QuestCadence.DAILY,
        )


def test_demo_rewards_catalog_lookup() -> None:
    catalog = DemoRewardsCatalogRepository()

    assert catalog.get_quest("missing") is None
    assert catalog.get_achievement("missing") is None
    assert catalog.get_reward("missing") is None
    assert catalog.get_decoration("missing") is None
    assert len(catalog.list_decorations()) == 3


def test_get_rewards_inventory(quest_service: QuestAchievementService) -> None:
    quest_service.seed_progress_records()
    inventory = quest_service.get_rewards_inventory()

    assert inventory.melody_points == 0
    assert inventory.unlocked_decorations == []


def test_completion_percentage_with_zero_target() -> None:
    from musicbloom.rewards.evaluator import completion_percentage

    assert completion_percentage(1, 0) == 0.0


def test_claim_missing_reward_definition_raises(
    quest_service: QuestAchievementService,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    quest_service.seed_progress_records()
    catalog = quest_service._rewards_catalog
    quest = quest_service._quest_progress.ensure_progress(
        user_id=quest_service._user_id,
        quest_id="daily-complete-three-tracks",
        period_key=period_key_for_cadence(QuestCadence.DAILY, datetime.now(tz=UTC)),
    )
    quest.progress = 3
    quest.completed_at = datetime.now(tz=UTC)
    quest.status = "completed"

    def broken_get_reward(reward_id: str):
        return None

    monkeypatch.setattr(catalog, "get_reward", broken_get_reward)

    with pytest.raises(RewardNotFoundError):
        quest_service.claim_quest("daily-complete-three-tracks")


def test_evaluate_skips_locked_and_claimed_entries(
    quest_service: QuestAchievementService,
) -> None:
    quest_service.seed_progress_records()
    progress = quest_service._user_progress.require_for_user(quest_service._user_id)
    progress.level = 0
    now = datetime.now(tz=UTC)
    daily_period = period_key_for_cadence(QuestCadence.DAILY, now)

    track = quest_service._catalog_service.get_track("demo-track-001")
    assert track is not None
    quest_service.evaluate_after_listening_event(
        track=track,
        event_type=ListeningEventType.COMPLETED,
        occurred_at=now,
        validated_listening_delta_ms=0,
        completion_awarded=True,
    )

    progress.level = 1
    claimed_quest = quest_service._quest_progress.ensure_progress(
        user_id=quest_service._user_id,
        quest_id="daily-complete-three-tracks",
        period_key=daily_period,
    )
    claimed_quest.claimed_at = now
    claimed_achievement = quest_service._achievement_progress.ensure_progress(
        user_id=quest_service._user_id,
        achievement_id="achievement-first-bloom",
    )
    claimed_achievement.claimed_at = now
    quest_service._quest_progress._db.flush()

    quest_service.evaluate_after_listening_event(
        track=track,
        event_type=ListeningEventType.PROGRESS,
        occurred_at=now,
        validated_listening_delta_ms=120_000,
        completion_awarded=False,
    )


def test_claim_achievement_missing_decoration_raises(
    quest_service: QuestAchievementService,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    quest_service.seed_progress_records()
    achievement = quest_service._achievement_progress.ensure_progress(
        user_id=quest_service._user_id,
        achievement_id="achievement-first-bloom",
    )
    quest_service._achievement_progress.save_progress(
        record=achievement,
        progress=1,
        completed=True,
    )
    catalog = quest_service._rewards_catalog

    def broken_get_decoration(decoration_id: str):
        return None

    monkeypatch.setattr(catalog, "get_decoration", broken_get_decoration)

    with pytest.raises(RewardNotFoundError):
        quest_service.claim_achievement("achievement-first-bloom")


def test_claim_reward_rejects_locked_and_duplicate_claim_record(
    quest_service: QuestAchievementService,
) -> None:
    quest_service.seed_progress_records()
    progress = quest_service._user_progress.require_for_user(quest_service._user_id)
    progress.level = 0

    with pytest.raises(RewardNotClaimableError, match="locked"):
        quest_service.claim_quest("daily-complete-three-tracks")

    progress.level = 1
    now = datetime.now(tz=UTC)
    period_key = period_key_for_cadence(QuestCadence.DAILY, now)
    quest = quest_service._quest_progress.ensure_progress(
        user_id=quest_service._user_id,
        quest_id="daily-complete-three-tracks",
        period_key=period_key,
    )
    quest_service._quest_progress.save_progress(
        record=quest,
        status="completed",
        progress=3,
        completed=True,
    )
    quest_service._reward_claims.add_claim(
        user_id=quest_service._user_id,
        reward_id="reward-daily-tracks",
        source_type="quest",
        source_id="daily-complete-three-tracks",
        melody_points_granted=25,
    )

    with pytest.raises(RewardAlreadyClaimedError):
        quest_service.claim_quest("daily-complete-three-tracks")


def test_claim_decoration_reward_missing_decoration_id_raises(
    quest_service: QuestAchievementService,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    quest_service.seed_progress_records()
    quest = quest_service._quest_progress.ensure_progress(
        user_id=quest_service._user_id,
        quest_id="daily-three-artists",
        period_key=period_key_for_cadence(QuestCadence.DAILY, datetime.now(tz=UTC)),
    )
    quest_service._quest_progress.save_progress(
        record=quest,
        status="completed",
        progress=3,
        completed=True,
    )
    broken_reward = Reward(
        id="reward-daily-artists",
        reward_type=RewardType.DECORATION_UNLOCK,
        decoration_id=None,
        description="Broken decoration reward",
    )

    def broken_get_reward(reward_id: str) -> Reward | None:
        if reward_id == broken_reward.id:
            return broken_reward
        return quest_service._rewards_catalog.get_reward(reward_id)

    monkeypatch.setattr(
        quest_service._rewards_catalog,
        "get_reward",
        broken_get_reward,
    )

    with pytest.raises(RewardNotFoundError, match="missing decoration_id"):
        quest_service.claim_quest("daily-three-artists")


def test_inventory_skips_missing_decoration_definition(
    quest_service: QuestAchievementService,
) -> None:
    quest_service.seed_progress_records()
    quest_service._decoration_unlocks.unlock(
        user_id=quest_service._user_id,
        decoration_id="missing-decoration",
    )

    inventory = quest_service.get_rewards_inventory()

    assert inventory.unlocked_decorations == []


def test_count_distinct_helpers_ignore_unknown_tracks(
    quest_service: QuestAchievementService,
) -> None:
    assert quest_service._count_distinct_artists(["missing-track"]) == 0
    assert quest_service._count_distinct_genres(["missing-track"]) == 0


def test_claim_quest_unlocks_decoration_reward(
    quest_service: QuestAchievementService,
) -> None:
    quest_service.seed_progress_records()
    quest = quest_service._quest_progress.ensure_progress(
        user_id=quest_service._user_id,
        quest_id="daily-three-artists",
        period_key=period_key_for_cadence(QuestCadence.DAILY, datetime.now(tz=UTC)),
    )
    quest_service._quest_progress.save_progress(
        record=quest,
        status="completed",
        progress=3,
        completed=True,
    )

    result = quest_service.claim_quest("daily-three-artists")

    assert result.decoration_unlocked is not None
    assert result.decoration_unlocked.id == "decoration-lantern-001"


def test_claim_reward_with_unhandled_reward_type(
    quest_service: QuestAchievementService,
) -> None:
    unhandled_reward = Reward.model_construct(
        id="reward-unhandled",
        reward_type=object(),
        melody_points=0,
        decoration_id=None,
        description="Unhandled reward type for branch coverage",
    )

    result = quest_service._claim_reward(
        source_type="quest",
        source_id="unhandled-reward-quest",
        reward=unhandled_reward,
        status=ProgressStatus.COMPLETED,
        on_claimed=lambda: None,
    )

    assert result.melody_points_granted == 0
    assert result.decoration_unlocked is None
