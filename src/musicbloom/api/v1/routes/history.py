"""Recent Blooms listening history routes."""

from typing import Annotated

from fastapi import APIRouter, Query

from musicbloom.dependencies import ProgressionServiceDep
from musicbloom.models.progression import RecentBloomsResponse

router = APIRouter(prefix="/history", tags=["history"])


@router.get(
    "/recent",
    response_model=RecentBloomsResponse,
    summary="List recent blooms",
    description=(
        "Return recently played, completed, or skipped tracks for the current "
        "demo user, enriched with catalog title, artist, and artwork."
    ),
)
def get_recent_blooms(
    progression_service: ProgressionServiceDep,
    limit: Annotated[int, Query(ge=1, le=100, description="Maximum items")] = 50,
) -> RecentBloomsResponse:
    """Return Recent Blooms listening history."""
    return progression_service.get_recent_blooms(limit=limit)
