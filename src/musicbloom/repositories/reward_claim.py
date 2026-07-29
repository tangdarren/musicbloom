"""Reward claim repository."""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from musicbloom.db.models.reward_claim import RewardClaim


class RewardClaimRepository:
    """Database access for reward claim history."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def get_for_source(
        self,
        *,
        user_id: int,
        source_type: str,
        source_id: str,
    ) -> RewardClaim | None:
        """Return an existing claim for a quest or achievement source."""
        return self._db.scalar(
            select(RewardClaim).where(
                RewardClaim.user_id == user_id,
                RewardClaim.source_type == source_type,
                RewardClaim.source_id == source_id,
            ),
        )

    def add_claim(
        self,
        *,
        user_id: int,
        reward_id: str,
        source_type: str,
        source_id: str,
        melody_points_granted: int,
        decoration_id: str | None = None,
        claimed_at: datetime | None = None,
    ) -> RewardClaim:
        """Persist a reward claim record."""
        claim = RewardClaim(
            user_id=user_id,
            reward_id=reward_id,
            source_type=source_type,
            source_id=source_id,
            melody_points_granted=melody_points_granted,
            decoration_id=decoration_id,
            claimed_at=claimed_at or datetime.now(tz=UTC),
        )
        self._db.add(claim)
        self._db.flush()
        self._db.refresh(claim)
        return claim

    def list_for_user(self, user_id: int) -> list[RewardClaim]:
        """Return reward claims for a user ordered by claim time."""
        return list(
            self._db.scalars(
                select(RewardClaim)
                .where(RewardClaim.user_id == user_id)
                .order_by(RewardClaim.claimed_at.desc()),
            ),
        )
