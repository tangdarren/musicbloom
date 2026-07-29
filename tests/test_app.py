"""Tests for the MusicBloom FastAPI application."""

from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from musicbloom import __version__
from musicbloom.api.app import create_app
from musicbloom.config import Settings
from musicbloom.constants import API_TITLE, SERVICE_NAME


def test_root_endpoint_status_code(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200


def test_root_endpoint_response_structure(client: TestClient) -> None:
    response = client.get("/")
    data = response.json()

    assert data == {
        "name": "MusicBloom",
        "tagline": "Grow your music garden, one song at a time.",
        "version": __version__,
    }


def test_health_endpoint_status_code(client: TestClient) -> None:
    response = client.get("/api/health")
    assert response.status_code == 200


def test_health_endpoint_response_structure(client: TestClient) -> None:
    response = client.get("/api/health")
    data = response.json()

    assert data == {
        "status": "healthy",
        "service": SERVICE_NAME,
    }


def test_v1_health_endpoint(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "service": SERVICE_NAME,
    }


def test_fastapi_metadata(test_app) -> None:
    assert test_app.title == API_TITLE
    assert test_app.version == __version__


def test_create_app_runs_database_initialization(test_engine) -> None:
    application = create_app(
        settings=Settings(demo_mode=True),
        engine=test_engine,
    )
    with TestClient(application):
        assert application.title == API_TITLE


def test_static_demo_audio_is_served(client: TestClient) -> None:
    response = client.get("/static/demo/audio/morning-dew-waltz.wav")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("audio/")


def test_create_app_skips_static_mount_when_directory_missing(
    test_engine,
) -> None:
    static_dir = Path(__file__).resolve().parents[1] / "static"

    with patch.object(Path, "is_dir", autospec=True) as is_dir:
        is_dir.side_effect = lambda self: self != static_dir
        application = create_app(
            settings=Settings(demo_mode=True),
            engine=test_engine,
        )

    with TestClient(application) as test_client:
        response = test_client.get("/static/demo/audio/morning-dew-waltz.wav")

    assert response.status_code == 404
