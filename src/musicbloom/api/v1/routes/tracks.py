"""Demo catalog track routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from musicbloom.api.v1.schemas.catalog import PaginatedTrackResponse, Track
from musicbloom.dependencies import get_catalog_service
from musicbloom.models.catalog import TrackMood
from musicbloom.services.catalog import CatalogService

router = APIRouter(prefix="/tracks", tags=["tracks"])


@router.get(
    "",
    response_model=PaginatedTrackResponse,
    summary="List demo tracks",
    description=(
        "Return a paginated collection of fictional demo tracks. "
        "Supports optional filtering by artist, album, genre, and mood."
    ),
)
def list_tracks(
    catalog_service: Annotated[CatalogService, Depends(get_catalog_service)],
    page: Annotated[
        int,
        Query(ge=1, description="Page number (1-indexed)"),
    ] = 1,
    page_size: Annotated[
        int,
        Query(ge=1, le=100, description="Number of tracks per page"),
    ] = 20,
    artist: Annotated[
        str | None,
        Query(description="Filter by artist name or identifier"),
    ] = None,
    album: Annotated[
        str | None,
        Query(description="Filter by album title or identifier"),
    ] = None,
    genre: Annotated[
        str | None,
        Query(description="Filter by genre label"),
    ] = None,
    mood: Annotated[
        TrackMood | None,
        Query(description="Filter by track mood"),
    ] = None,
) -> PaginatedTrackResponse:
    """List demo tracks with pagination and optional filters."""
    return catalog_service.list_tracks(
        page=page,
        page_size=page_size,
        artist=artist,
        album=album,
        genre=genre,
        mood=mood,
    )


@router.get(
    "/{track_id}",
    response_model=Track,
    summary="Get demo track",
    description="Return a single demo track by its stable identifier.",
    responses={404: {"description": "Track not found"}},
)
def get_track(
    track_id: str,
    catalog_service: Annotated[CatalogService, Depends(get_catalog_service)],
) -> Track:
    """Return a single demo track."""
    track = catalog_service.get_track(track_id)
    if track is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Track '{track_id}' was not found",
        )
    return track
