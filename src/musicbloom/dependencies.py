"""FastAPI dependency providers."""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from musicbloom.config import Settings
from musicbloom.repositories.demo_catalog import DemoCatalogRepository
from musicbloom.repositories.in_memory_player import InMemoryPlayerSessionRepository
from musicbloom.services.catalog import CatalogService
from musicbloom.services.player import PlayerService


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()


@lru_cache
def get_demo_catalog_repository() -> DemoCatalogRepository:
    """Return cached demo catalog repository."""
    return DemoCatalogRepository()


@lru_cache
def get_player_session_repository() -> InMemoryPlayerSessionRepository:
    """Return cached in-memory player session repository."""
    return InMemoryPlayerSessionRepository()


def get_catalog_service(
    repository: Annotated[
        DemoCatalogRepository,
        Depends(get_demo_catalog_repository),
    ],
) -> CatalogService:
    """Return catalog service backed by the demo repository."""
    return CatalogService(repository)


def get_player_service(
    player_repository: Annotated[
        InMemoryPlayerSessionRepository,
        Depends(get_player_session_repository),
    ],
    catalog_repository: Annotated[
        DemoCatalogRepository,
        Depends(get_demo_catalog_repository),
    ],
) -> PlayerService:
    """Return player service backed by in-memory session storage."""
    return PlayerService(player_repository, catalog_repository)


CatalogServiceDep = Annotated[CatalogService, Depends(get_catalog_service)]
PlayerServiceDep = Annotated[PlayerService, Depends(get_player_service)]
