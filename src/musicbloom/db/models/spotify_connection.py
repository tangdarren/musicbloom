"""Spotify OAuth connection database entity."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from musicbloom.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from musicbloom.db.models.user_profile import UserProfile


class SpotifyConnectionRecord(Base, TimestampMixin):
    """Encrypted Spotify OAuth tokens for a MusicBloom user."""

    __tablename__ = "spotify_connections"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_spotify_connections_user_id"),
        UniqueConstraint(
            "spotify_user_id",
            name="uq_spotify_connections_spotify_user_id",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user_profiles.id", ondelete="CASCADE"),
        index=True,
    )
    spotify_user_id: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        index=True,
    )
    display_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    encrypted_access_token: Mapped[str] = mapped_column(Text, nullable=False)
    encrypted_refresh_token: Mapped[str] = mapped_column(Text, nullable=False)
    token_expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    scopes: Mapped[str] = mapped_column(String(512), nullable=False)
    last_error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_error_message: Mapped[str | None] = mapped_column(String(512), nullable=True)

    user: Mapped[UserProfile] = relationship(back_populates="spotify_connection")
