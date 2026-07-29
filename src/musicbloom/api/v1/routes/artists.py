"""Demo catalog artist routes."""

from typing import Annotated

from fastapi import APIRouter, Depends

from musicbloom.api.v1.schemas.catalog import Artist
from musicbloom.dependencies import get_catalog_service
from musicbloom.services.catalog import CatalogService

router = APIRouter(prefix="/artists", tags=["artists"])


@router.get(
    "",
    response_model=list[Artist],
    summary="List demo artists",
    description="Return all fictional artists included in the demo catalog.",
)
def list_artists(
    catalog_service: Annotated[CatalogService, Depends(get_catalog_service)],
) -> list[Artist]:
    """List all demo artists."""
    return catalog_service.list_artists()
