"""Shared pytest fixtures."""

import pytest

from musicbloom.dependencies import get_settings


@pytest.fixture(autouse=True)
def clear_settings_cache() -> None:
    """Ensure settings are reloaded for each test."""
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
