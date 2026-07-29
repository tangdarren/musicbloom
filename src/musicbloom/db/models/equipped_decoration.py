"""Equipped decoration database entity."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from musicbloom.db.base import Base, TimestampMixin


class EquippedDecoration(Base, TimestampMixin):
    """Decoration equipped in a garden slot."""

    __tablename__ = "equipped_decorations"
    __table_args__ = (
        UniqueConstraint("user_id", "slot", name="uq_equipped_decorations_user_slot"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user_profiles.id", ondelete="CASCADE"),
        index=True,
    )
    decoration_id: Mapped[str] = mapped_column(String(64), nullable=False)
    slot: Mapped[str] = mapped_column(String(64), nullable=False)
    equipped_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
