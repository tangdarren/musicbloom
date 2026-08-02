"""Favorite track database entity."""

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from musicbloom.db.base import Base, TimestampMixin


class FavoriteTrack(Base, TimestampMixin):
    """Persisted favorite track for a demo user."""

    __tablename__ = "favorite_tracks"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "track_id",
            name="uq_favorite_tracks_user_track",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user_profiles.id", ondelete="CASCADE"),
        index=True,
    )
    track_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
