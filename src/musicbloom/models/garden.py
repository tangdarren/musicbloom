"""Domain models for the interactive music garden."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from musicbloom.models.progression import DailyListeningStreak, UserLevel
from musicbloom.models.rewards import (
    DecorationDefinition,
    DecorationUnlock,
    ProgressStatus,
)


class GardenMood(StrEnum):
    """Derived garden atmosphere based on listening progress."""

    SERENE = "serene"
    CHEERFUL = "cheerful"
    BLOOMING = "blooming"


class ArtistFlower(BaseModel):
    """Flower representing listening activity for a favorite artist."""

    artist_id: str = Field(description="Artist identifier")
    artist_name: str = Field(description="Artist display name")
    completions: int = Field(ge=0, description="Completed tracks by this artist")
    bloom_stage: int = Field(
        ge=0,
        le=3,
        description="Visual bloom stage from 0 (bud) to 3 (full bloom)",
    )


class ListeningMilestonePlant(BaseModel):
    """Plant representing a listening milestone."""

    id: str = Field(description="Stable milestone identifier")
    title: str = Field(description="Milestone title")
    description: str = Field(description="Milestone description")
    target: int = Field(ge=1, description="Target value for the milestone")
    progress: int = Field(ge=0, description="Current progress toward the milestone")
    unlocked: bool = Field(description="Whether the milestone plant has grown in")


class EquippedDecorationView(BaseModel):
    """Decoration currently placed in the garden."""

    decoration: DecorationDefinition = Field(description="Decoration metadata")
    slot: str = Field(description="Garden slot where the decoration is placed")
    equipped_at: datetime = Field(description="UTC timestamp when equipped")


class DecorationCatalogEntry(BaseModel):
    """Decoration catalog entry with unlock and equip status."""

    decoration: DecorationDefinition = Field(description="Decoration metadata")
    unlocked: bool = Field(description="Whether the user has unlocked this decoration")
    equipped: bool = Field(description="Whether the decoration is currently equipped")


class RecentAchievement(BaseModel):
    """Recent achievement activity for the garden sidebar."""

    achievement_id: str = Field(description="Achievement identifier")
    title: str = Field(description="Achievement title")
    status: ProgressStatus = Field(description="Current achievement status")
    completed_at: datetime | None = Field(default=None)


class GardenProfileView(BaseModel):
    """Garden profile metadata."""

    garden_name: str = Field(description="User-defined garden name")
    theme: str = Field(description="Garden visual theme")


class GardenState(BaseModel):
    """Aggregated garden state derived from real backend progress."""

    profile: GardenProfileView = Field(description="Garden profile metadata")
    mood: GardenMood = Field(description="Current garden mood")
    level: UserLevel = Field(description="Current user level and experience")
    melody_points: int = Field(ge=0, description="Current Melody Points balance")
    streak: DailyListeningStreak = Field(description="Daily listening streak")
    artist_flowers: list[ArtistFlower] = Field(
        default_factory=list,
        description="Flowers representing favorite artists",
    )
    milestone_plants: list[ListeningMilestonePlant] = Field(
        default_factory=list,
        description="Plants representing listening milestones",
    )
    unlocked_decorations: list[DecorationUnlock] = Field(
        default_factory=list,
        description="Decorations unlocked by the user",
    )
    equipped_decorations: list[EquippedDecorationView] = Field(
        default_factory=list,
        description="Decorations currently equipped in the garden",
    )
    recent_achievements: list[RecentAchievement] = Field(
        default_factory=list,
        description="Recently completed or active achievements",
    )
    tracks_completed: int = Field(
        ge=0,
        description="Total tracks completed by the user",
    )
    total_listening_minutes: int = Field(
        ge=0,
        description="Total validated listening time in minutes",
    )


class EquipDecorationResult(BaseModel):
    """Result of equipping a decoration."""

    decoration: DecorationDefinition = Field(description="Equipped decoration")
    slot: str = Field(description="Slot where the decoration was placed")
    equipped_at: datetime = Field(description="UTC equip timestamp")
