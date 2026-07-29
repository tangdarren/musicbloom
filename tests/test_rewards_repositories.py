"""Tests for reward repositories."""

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from musicbloom.db.init import get_demo_user
from musicbloom.repositories.decoration_unlock import DecorationUnlockRepository
from musicbloom.repositories.reward_claim import RewardClaimRepository


def test_reward_claim_repository(db_session: Session) -> None:
    user = get_demo_user(db_session)
    repository = RewardClaimRepository(db_session)

    claim = repository.add_claim(
        user_id=user.id,
        reward_id="reward-daily-tracks",
        source_type="quest",
        source_id="daily-complete-three-tracks",
        melody_points_granted=25,
        claimed_at=datetime.now(tz=UTC),
    )

    assert repository.get_for_source(
        user_id=user.id,
        source_type="quest",
        source_id="daily-complete-three-tracks",
    ) == claim
    assert len(repository.list_for_user(user.id)) == 1


def test_decoration_unlock_repository(db_session: Session) -> None:
    user = get_demo_user(db_session)
    repository = DecorationUnlockRepository(db_session)

    first = repository.unlock(
        user_id=user.id,
        decoration_id="decoration-lantern-001",
    )
    second = repository.unlock(
        user_id=user.id,
        decoration_id="decoration-lantern-001",
    )

    assert first.id == second.id
    assert len(repository.list_for_user(user.id)) == 1
