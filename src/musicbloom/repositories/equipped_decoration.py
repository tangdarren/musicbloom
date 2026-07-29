"""Equipped decoration repository."""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from musicbloom.db.models.equipped_decoration import EquippedDecoration


class EquippedDecorationRepository:
    """Database access for equipped decorations."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def list_for_user(self, user_id: int) -> list[EquippedDecoration]:
        """Return equipped decorations for a user."""
        return list(
            self._db.scalars(
                select(EquippedDecoration).where(
                    EquippedDecoration.user_id == user_id,
                ),
            ),
        )

    def equip(
        self,
        *,
        user_id: int,
        decoration_id: str,
        slot: str,
    ) -> EquippedDecoration:
        """Equip or replace a decoration in a slot."""
        existing = self._db.scalar(
            select(EquippedDecoration).where(
                EquippedDecoration.user_id == user_id,
                EquippedDecoration.slot == slot,
            ),
        )
        if existing is not None:
            existing.decoration_id = decoration_id
            existing.equipped_at = datetime.now(tz=UTC)
            self._db.flush()
            self._db.refresh(existing)
            return existing

        decoration = EquippedDecoration(
            user_id=user_id,
            decoration_id=decoration_id,
            slot=slot,
            equipped_at=datetime.now(tz=UTC),
        )
        self._db.add(decoration)
        self._db.flush()
        self._db.refresh(decoration)
        return decoration
