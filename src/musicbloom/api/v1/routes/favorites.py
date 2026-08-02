"""Favorite track routes."""

from fastapi import APIRouter, Response, status

from musicbloom.api.v1.schemas.favorites import (
    FavoritesListResponse,
    FavoriteTrackResponse,
)
from musicbloom.dependencies import FavoritesServiceDep

router = APIRouter(tags=["favorites"])


@router.get(
    "/favorites",
    response_model=FavoritesListResponse,
    summary="List favorite tracks",
    description=(
        "Return favorited demo catalog tracks for the current demo user, "
        "newest first."
    ),
)
def list_favorites(
    favorites_service: FavoritesServiceDep,
) -> FavoritesListResponse:
    """Return the current user's favorite tracks."""
    return favorites_service.list_favorites()


@router.put(
    "/favorites/{track_id}",
    response_model=FavoriteTrackResponse,
    summary="Favorite a track",
    description=(
        "Add a demo catalog track to favorites. Repeating the request is safe "
        "and returns the existing favorite."
    ),
)
def add_favorite(
    track_id: str,
    favorites_service: FavoritesServiceDep,
) -> FavoriteTrackResponse:
    """Favorite a track for the current demo user."""
    return favorites_service.add_favorite(track_id)


@router.delete(
    "/favorites/{track_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Unfavorite a track",
    description=(
        "Remove a track from favorites. Repeating the request is safe when the "
        "track is already unfavorited."
    ),
)
def remove_favorite(
    track_id: str,
    favorites_service: FavoritesServiceDep,
) -> Response:
    """Remove a track from the current user's favorites."""
    favorites_service.remove_favorite(track_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
