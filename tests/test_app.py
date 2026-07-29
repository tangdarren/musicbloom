"""Tests for the MusicBloom FastAPI application."""

from fastapi.testclient import TestClient

from musicbloom import __version__
from musicbloom.api.app import API_TITLE, SERVICE_NAME, app

client = TestClient(app)


def test_root_endpoint_status_code() -> None:
    response = client.get("/")
    assert response.status_code == 200


def test_root_endpoint_response_structure() -> None:
    response = client.get("/")
    data = response.json()

    assert data == {
        "name": "MusicBloom",
        "tagline": "Grow your music garden, one song at a time.",
        "version": __version__,
    }


def test_health_endpoint_status_code() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200


def test_health_endpoint_response_structure() -> None:
    response = client.get("/api/health")
    data = response.json()

    assert data == {
        "status": "healthy",
        "service": SERVICE_NAME,
    }


def test_fastapi_metadata() -> None:
    assert app.title == API_TITLE
    assert app.version == __version__
