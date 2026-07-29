"""Progression read routes."""

from fastapi import APIRouter

from musicbloom.api.v1.schemas.progression import (
    DailyListeningStreakResponse,
    ListeningStatisticsResponse,
    ProgressSummaryResponse,
)
from musicbloom.dependencies import ProgressionServiceDep

router = APIRouter(tags=["progress"])


@router.get(
    "/progress",
    response_model=ProgressSummaryResponse,
    summary="Get progression summary",
    description="Return Melody Points, level, streak, and listening statistics.",
)
def get_progress(
    progression_service: ProgressionServiceDep,
) -> ProgressSummaryResponse:
    """Return the current user's progression summary."""
    return progression_service.get_progress_summary()


@router.get(
    "/stats",
    response_model=ListeningStatisticsResponse,
    summary="Get listening statistics",
    description="Return aggregate listening metrics for the current user.",
)
def get_stats(
    progression_service: ProgressionServiceDep,
) -> ListeningStatisticsResponse:
    """Return listening statistics."""
    return progression_service.get_statistics()


@router.get(
    "/streak",
    response_model=DailyListeningStreakResponse,
    summary="Get daily listening streak",
    description="Return UTC-based daily listening streak information.",
)
def get_streak(
    progression_service: ProgressionServiceDep,
) -> DailyListeningStreakResponse:
    """Return the current daily listening streak."""
    return progression_service.get_streak()
