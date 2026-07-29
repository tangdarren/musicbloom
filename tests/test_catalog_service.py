"""Unit tests for the catalog service."""

import pytest

from musicbloom.models.catalog import TrackMood
from musicbloom.repositories.demo_catalog import DemoCatalogRepository
from musicbloom.services.catalog import CatalogService


@pytest.fixture
def catalog_service() -> CatalogService:
    return CatalogService(DemoCatalogRepository())


def test_list_artists_returns_demo_artists(catalog_service: CatalogService) -> None:
    artists = catalog_service.list_artists()
    assert len(artists) == 7


def test_list_albums_returns_demo_albums(catalog_service: CatalogService) -> None:
    albums = catalog_service.list_albums()
    assert len(albums) == 7


def test_get_track_returns_known_track(catalog_service: CatalogService) -> None:
    track = catalog_service.get_track("demo-track-004")
    assert track is not None
    assert track.title == "Bubblegum Breeze"


def test_get_track_returns_none_for_unknown_id(catalog_service: CatalogService) -> None:
    assert catalog_service.get_track("unknown") is None


def test_list_tracks_returns_paginated_response(
    catalog_service: CatalogService,
) -> None:
    response = catalog_service.list_tracks(page=1, page_size=3)

    assert response.total == 8
    assert response.page == 1
    assert response.page_size == 3
    assert response.total_pages == 3
    assert len(response.items) == 3


def test_list_tracks_second_page(catalog_service: CatalogService) -> None:
    response = catalog_service.list_tracks(page=3, page_size=3)

    assert len(response.items) == 2
    assert response.total_pages == 3


def test_list_tracks_empty_page_when_beyond_results(
    catalog_service: CatalogService,
) -> None:
    response = catalog_service.list_tracks(page=10, page_size=3)

    assert response.items == []
    assert response.total == 8


def test_filter_tracks_by_artist_name(catalog_service: CatalogService) -> None:
    response = catalog_service.list_tracks(
        page=1,
        page_size=20,
        artist="Nightshade",
    )

    assert response.total == 2
    assert all("Nightshade" in track.artist_name for track in response.items)


def test_filter_tracks_by_artist_id(catalog_service: CatalogService) -> None:
    response = catalog_service.list_tracks(
        page=1,
        page_size=20,
        artist="artist-luna-sprout",
    )

    assert response.total == 1
    assert response.items[0].title == "Sunbeam Carousel"


def test_filter_tracks_by_album_title(catalog_service: CatalogService) -> None:
    response = catalog_service.list_tracks(
        page=1,
        page_size=20,
        album="Moonlit",
    )

    assert response.total == 2


def test_filter_tracks_by_album_id(catalog_service: CatalogService) -> None:
    response = catalog_service.list_tracks(
        page=1,
        page_size=20,
        album="album-cloud-garden",
    )

    assert response.total == 1


def test_filter_tracks_by_genre(catalog_service: CatalogService) -> None:
    response = catalog_service.list_tracks(
        page=1,
        page_size=20,
        genre="ambient dusk",
    )

    assert response.total == 2


def test_filter_tracks_by_mood(catalog_service: CatalogService) -> None:
    response = catalog_service.list_tracks(
        page=1,
        page_size=20,
        mood=TrackMood.ENERGETIC,
    )

    assert response.total == 2
    assert all(track.mood == TrackMood.ENERGETIC for track in response.items)


def test_filter_tracks_with_no_matches(catalog_service: CatalogService) -> None:
    response = catalog_service.list_tracks(
        page=1,
        page_size=20,
        genre="nonexistent-genre",
    )

    assert response.total == 0
    assert response.total_pages == 0
    assert response.items == []
