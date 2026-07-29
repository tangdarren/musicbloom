"""User profile database entity."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from musicbloom.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from musicbloom.db.models.garden_profile import GardenProfile
    from musicbloom.db.models.player_session import PlayerSessionRecord
    from musicbloom.db.models.spotify_connection import SpotifyConnectionRecord
    from musicbloom.db.models.user_progress import UserProgress


class UserProfile(Base, TimestampMixin):
    """Persistent user profile."""

    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(128))
    avatar_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    is_demo_user: Mapped[bool] = mapped_column(Boolean, default=False, index=True)

    player_session: Mapped[PlayerSessionRecord | None] = relationship(
        back_populates="user",
        uselist=False,
    )
    garden_profile: Mapped[GardenProfile | None] = relationship(
        back_populates="user",
        uselist=False,
    )
    progress: Mapped[UserProgress | None] = relationship(
        back_populates="user",
        uselist=False,
    )
    spotify_connection: Mapped[SpotifyConnectionRecord | None] = relationship(
        back_populates="user",
        uselist=False,
    )
