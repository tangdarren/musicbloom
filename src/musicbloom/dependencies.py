"""FastAPI dependency providers."""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from musicbloom.config import Settings
from musicbloom.repositories.demo_catalog import DemoCatalogRepository
from musicbloom.services.catalog import CatalogService


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()


@lru_cache
def get_demo_catalog_repository() -> DemoCatalogRepository:
    """Return cached demo catalog repository."""
    return DemoCatalogRepository()


def get_catalog_service(
    repository: Annotated[
        DemoCatalogRepository,
        Depends(get_demo_catalog_repository),
    ],
) -> CatalogService:
    """Return catalog service backed by the demo repository."""
    return CatalogService(repository)


CatalogServiceDep = Annotated[CatalogService, Depends(get_catalog_service)]
