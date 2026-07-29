"""Tests for the MusicBloom FastAPI application."""

from fastapi.testclient import TestClient

from musicbloom import __version__
from musicbloom.api.app import app, create_app
from musicbloom.constants import API_TITLE, SERVICE_NAME

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


def test_v1_health_endpoint() -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "service": SERVICE_NAME,
    }


def test_fastapi_metadata() -> None:
    assert app.title == API_TITLE
    assert app.version == __version__


def test_create_app_uses_provided_settings() -> None:
    from musicbloom.config import Settings

    settings = Settings(debug=False, cors_origins=["https://example.com"])
    test_app = create_app(settings=settings)

    assert test_app.debug is False
