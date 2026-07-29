"""Shared pytest fixtures."""

from collections.abc import Iterator

import pytest

from musicbloom.dependencies import (
    get_demo_catalog_repository,
    get_player_session_repository,
    get_settings,
)


@pytest.fixture(autouse=True)
def clear_dependency_caches() -> Iterator[None]:
    """Ensure cached dependencies are reloaded for each test."""
    get_settings.cache_clear()
    get_demo_catalog_repository.cache_clear()
    get_player_session_repository.cache_clear()
    yield
    get_settings.cache_clear()
    get_demo_catalog_repository.cache_clear()
    get_player_session_repository.cache_clear()
