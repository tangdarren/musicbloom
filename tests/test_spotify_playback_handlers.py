"""Tests for Spotify playback exception handlers."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from musicbloom.api.v1.spotify_player_handlers import (
    register_spotify_playback_exception_handlers,
)
from musicbloom.services.spotify_playback_errors import SpotifyNoActiveDeviceError


def test_spotify_playback_exception_handler_returns_service_status_code() -> None:
    app = FastAPI()
    register_spotify_playback_exception_handlers(app)

    @app.get("/boom")
    def boom() -> None:
        raise SpotifyNoActiveDeviceError("no active device")

    client = TestClient(app)
    response = client.get("/boom")

    assert response.status_code == 409
    assert response.json()["detail"] == "no active device"
