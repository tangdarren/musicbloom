"""Garden profile database entity."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from musicbloom.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from musicbloom.db.models.user_profile import UserProfile


class GardenProfile(Base, TimestampMixin):
    """Persistent garden state for a user."""

    __tablename__ = "garden_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user_profiles.id", ondelete="CASCADE"),
        unique=True,
        index=True,
    )
    garden_name: Mapped[str] = mapped_column(String(128), nullable=False)
    theme: Mapped[str] = mapped_column(String(64), nullable=False)
    layout_data: Mapped[dict[str, object]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    user: Mapped[UserProfile] = relationship(back_populates="garden_profile")
