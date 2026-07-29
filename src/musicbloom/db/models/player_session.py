"""Player session database entity."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from musicbloom.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from musicbloom.db.models.user_profile import UserProfile


class PlayerSessionRecord(Base, TimestampMixin):
    """Persistent player session state for a user."""

    __tablename__ = "player_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user_profiles.id", ondelete="CASCADE"),
        unique=True,
        index=True,
    )
    state: Mapped[str] = mapped_column(String(16), nullable=False)
    volume_level: Mapped[float] = mapped_column(Float, nullable=False)
    shuffle: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    repeat_mode: Mapped[str] = mapped_column(String(8), nullable=False)
    queue_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    active_track: Mapped[dict[str, object] | None] = mapped_column(JSON, nullable=True)
    queue: Mapped[list[dict[str, object]]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

    user: Mapped[UserProfile] = relationship(back_populates="player_session")
