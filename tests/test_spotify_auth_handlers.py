"""Tests for Spotify auth exception handlers."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from musicbloom.api.v1.spotify_auth_handlers import (
    register_spotify_auth_exception_handlers,
)
from musicbloom.services.spotify_auth_errors import SpotifyConnectionNotFoundError


def test_spotify_auth_exception_handler_returns_service_status_code() -> None:
    app = FastAPI()
    register_spotify_auth_exception_handlers(app)

    @app.get("/boom")
    def boom() -> None:
        raise SpotifyConnectionNotFoundError("not connected")

    client = TestClient(app)
    response = client.get("/boom")

    assert response.status_code == 404
    assert response.json()["detail"] == "not connected"
