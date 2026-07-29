"""Tests for Spotify auth API endpoints."""

import httpx
import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from musicbloom.config import OAUTH_STATE_COOKIE, Settings
from musicbloom.dependencies import get_settings, get_spotify_oauth_client
from musicbloom.integrations.spotify.client import HttpSpotifyOAuthClient
from musicbloom.security.oauth_state import (
    build_signed_oauth_state,
    generate_oauth_state,
)


def _spotify_settings() -> Settings:
    return Settings(
        secret_key=SecretStr("development-secret-key-for-tests!!"),
        token_encryption_key=SecretStr("development-token-encryption-key"),
        spotify_client_id="test-client-id",
        spotify_client_secret=SecretStr("test-client-secret"),
        spotify_redirect_uri="http://127.0.0.1:8000/api/v1/auth/spotify/callback",
        spotify_frontend_success_redirect="http://localhost:5173/?spotify=connected",
        spotify_frontend_failure_redirect="http://localhost:5173/?spotify=error",
    )


def _mock_transport() -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/token":
            return httpx.Response(
                200,
                json={
                    "access_token": "access-token",
                    "refresh_token": "refresh-token",
                    "expires_in": 3600,
                    "token_type": "Bearer",
                    "scope": "user-read-email",
                },
            )
        if request.url.path == "/v1/me":
            return httpx.Response(
                200,
                json={"id": "spotify-user-123", "display_name": "Bloom Listener"},
            )
        return httpx.Response(404)

    return httpx.MockTransport(handler)


@pytest.fixture
def spotify_client(test_app) -> None:
    get_settings.cache_clear()
    test_app.dependency_overrides[get_settings] = _spotify_settings
    test_app.dependency_overrides[get_spotify_oauth_client] = (
        lambda: HttpSpotifyOAuthClient(transport=_mock_transport())
    )
    yield
    test_app.dependency_overrides.pop(get_settings, None)
    test_app.dependency_overrides.pop(get_spotify_oauth_client, None)
    get_settings.cache_clear()


def test_spotify_status_when_unconfigured(client: TestClient) -> None:
    response = client.get("/api/v1/auth/spotify/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "disconnected"
    assert payload["configured"] is False


def test_spotify_login_redirects_when_unconfigured(client: TestClient) -> None:
    response = client.get("/api/v1/auth/spotify/login", follow_redirects=False)

    assert response.status_code == 302
    assert "spotify=error" in response.headers["location"]
    assert "reason=not_configured" in response.headers["location"]


def test_spotify_login_sets_state_cookie(
    client: TestClient,
    spotify_client: None,
) -> None:
    response = client.get("/api/v1/auth/spotify/login", follow_redirects=False)

    assert response.status_code == 302
    assert "accounts.spotify.com/authorize" in response.headers["location"]
    assert OAUTH_STATE_COOKIE in response.cookies


def test_spotify_callback_completes_login(
    client: TestClient,
    spotify_client: None,
) -> None:
    settings = _spotify_settings()
    state = generate_oauth_state()
    signed_state = build_signed_oauth_state(state, settings.secret_key)  # type: ignore[arg-type]
    client.cookies.set(OAUTH_STATE_COOKIE, signed_state)

    response = client.get(
        f"/api/v1/auth/spotify/callback?code=auth-code&state={state}",
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["location"].endswith("spotify=connected")

    status = client.get("/api/v1/auth/spotify/status").json()
    assert status["status"] == "connected"
    assert status["spotify_user_id"] == "spotify-user-123"


def test_spotify_callback_denied_redirects_to_failure(
    client: TestClient,
    spotify_client: None,
) -> None:
    response = client.get(
        "/api/v1/auth/spotify/callback?error=access_denied",
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert "reason=denied" in response.headers["location"]


def test_spotify_callback_not_configured_redirect(
    client: TestClient,
    test_app,
) -> None:
    from musicbloom.dependencies import get_settings

    get_settings.cache_clear()
    test_app.dependency_overrides[get_settings] = lambda: Settings(
        spotify_client_id="test-client-id",
        spotify_client_secret=SecretStr("test-client-secret"),
        spotify_redirect_uri="http://127.0.0.1:8000/api/v1/auth/spotify/callback",
        spotify_frontend_failure_redirect="http://localhost:5173/?spotify=error",
    )

    response = client.get(
        "/api/v1/auth/spotify/callback?code=auth-code&state=state",
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert "reason=not_configured" in response.headers["location"]
    test_app.dependency_overrides.pop(get_settings, None)
    get_settings.cache_clear()


def test_spotify_disconnect(client: TestClient, spotify_client: None) -> None:
    settings = _spotify_settings()
    state = generate_oauth_state()
    signed_state = build_signed_oauth_state(state, settings.secret_key)  # type: ignore[arg-type]
    client.cookies.set(OAUTH_STATE_COOKIE, signed_state)
    client.get(f"/api/v1/auth/spotify/callback?code=auth-code&state={state}")

    response = client.delete("/api/v1/auth/spotify")

    assert response.status_code == 200
    assert response.json()["disconnected"] is True

    status = client.get("/api/v1/auth/spotify/status").json()
    assert status["status"] == "disconnected"
