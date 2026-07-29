"""Tests for Spotify playback API endpoints."""

from datetime import UTC, datetime, timedelta

import httpx
import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy.orm import Session

from musicbloom.config import Settings
from musicbloom.db.init import get_demo_user
from musicbloom.dependencies import (
    get_settings,
    get_spotify_oauth_client,
    get_spotify_playback_client,
)
from musicbloom.integrations.spotify.client import HttpSpotifyOAuthClient
from musicbloom.integrations.spotify.playback_client import HttpSpotifyPlaybackClient
from musicbloom.repositories.spotify_connection import SpotifyConnectionRepository
from musicbloom.security.token_encryption import TokenEncryptor


def _spotify_settings() -> Settings:
    return Settings(
        secret_key=SecretStr("development-secret-key-for-tests!!"),
        token_encryption_key=SecretStr("development-token-encryption-key"),
        spotify_client_id="test-client-id",
        spotify_client_secret=SecretStr("test-client-secret"),
        spotify_redirect_uri="http://127.0.0.1:8000/api/v1/auth/spotify/callback",
    )


def _playback_state() -> dict[str, object]:
    return {
        "device": {
            "id": "device-123",
            "is_active": True,
            "name": "Bloom Laptop",
            "type": "Computer",
            "volume_percent": 55,
        },
        "shuffle_state": False,
        "repeat_state": "off",
        "progress_ms": 42_000,
        "is_playing": True,
        "item": {
            "id": "track-123",
            "name": "Garden Echoes",
            "duration_ms": 210_000,
            "uri": "spotify:track:track-123",
            "artists": [{"name": "Petal & Pine"}],
            "album": {
                "name": "Greenhouse Echoes",
                "images": [{"url": "https://i.scdn.co/image/example.png"}],
            },
        },
    }


def _mock_playback_transport() -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v1/me/player/recently-played":
            return httpx.Response(200, json={"items": []})
        if request.url.path == "/v1/me/player" and request.method == "GET":
            return httpx.Response(200, json=_playback_state())
        if request.url.path.startswith("/v1/me/player/"):
            return httpx.Response(204)
        return httpx.Response(404)

    return httpx.MockTransport(handler)


@pytest.fixture
def spotify_playback_client(test_app, db_session: Session) -> None:
    user = get_demo_user(db_session)
    encryptor = TokenEncryptor(_spotify_settings().token_encryption_key)  # type: ignore[arg-type]
    SpotifyConnectionRepository(db_session).upsert_connection(
        user_id=user.id,
        spotify_user_id="spotify-user-123",
        display_name="Bloom Listener",
        encrypted_access_token=encryptor.encrypt("access-token"),
        encrypted_refresh_token=encryptor.encrypt("refresh-token"),
        token_expires_at=datetime.now(tz=UTC) + timedelta(hours=1),
        scopes="user-read-playback-state user-modify-playback-state",
    )
    get_settings.cache_clear()
    test_app.dependency_overrides[get_settings] = _spotify_settings
    test_app.dependency_overrides[get_spotify_oauth_client] = (
        lambda: HttpSpotifyOAuthClient(
            transport=httpx.MockTransport(lambda _: httpx.Response(404)),
        )
    )
    test_app.dependency_overrides[get_spotify_playback_client] = (
        lambda: HttpSpotifyPlaybackClient(transport=_mock_playback_transport())
    )
    yield
    test_app.dependency_overrides.pop(get_settings, None)
    test_app.dependency_overrides.pop(get_spotify_oauth_client, None)
    test_app.dependency_overrides.pop(get_spotify_playback_client, None)
    get_settings.cache_clear()


def test_get_spotify_player(
    client: TestClient,
    spotify_playback_client: None,
) -> None:
    response = client.get("/api/v1/spotify/player")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "playing"
    assert payload["track"]["title"] == "Garden Echoes"
    assert "access_token" not in response.text


def test_pause_spotify_player(
    client: TestClient,
    spotify_playback_client: None,
) -> None:
    response = client.put("/api/v1/spotify/player/pause")

    assert response.status_code == 200


def test_play_spotify_player(
    client: TestClient,
    spotify_playback_client: None,
) -> None:
    response = client.put("/api/v1/spotify/player/play")

    assert response.status_code == 200


def test_next_spotify_player(
    client: TestClient,
    spotify_playback_client: None,
) -> None:
    response = client.post("/api/v1/spotify/player/next")

    assert response.status_code == 200


def test_previous_spotify_player(
    client: TestClient,
    spotify_playback_client: None,
) -> None:
    response = client.post("/api/v1/spotify/player/previous")

    assert response.status_code == 200


def test_seek_spotify_player(
    client: TestClient,
    spotify_playback_client: None,
) -> None:
    response = client.put(
        "/api/v1/spotify/player/seek",
        json={"position_ms": 30_000},
    )

    assert response.status_code == 200


def test_set_spotify_volume(
    client: TestClient,
    spotify_playback_client: None,
) -> None:
    response = client.put(
        "/api/v1/spotify/player/volume",
        json={"level": 0.6},
    )

    assert response.status_code == 200


def test_spotify_player_unconfigured(client: TestClient) -> None:
    response = client.get("/api/v1/spotify/player")

    assert response.status_code == 200
    payload = response.json()
    assert payload["configured"] is False
    assert payload["connected"] is False
