"""Decoration unlock database entity."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from musicbloom.db.base import Base


class DecorationUnlockRecord(Base):
    """Decoration unlocked by a user."""

    __tablename__ = "decoration_unlocks"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "decoration_id",
            name="uq_decoration_unlocks_user_decoration",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user_profiles.id", ondelete="CASCADE"),
        index=True,
    )
    decoration_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    unlocked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
