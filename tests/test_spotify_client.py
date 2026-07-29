"""Tests for Spotify OAuth HTTP client."""

import asyncio

import httpx

from musicbloom.integrations.spotify.client import HttpSpotifyOAuthClient


def _build_transport() -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/token":
            body = request.content.decode()
            if "grant_type=authorization_code" in body:
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
            if "grant_type=refresh_token" in body:
                return httpx.Response(
                    200,
                    json={
                        "access_token": "refreshed-access-token",
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
        return httpx.Response(404, json={"error": "not found"})

    return httpx.MockTransport(handler)


def test_exchange_code_and_fetch_profile() -> None:
    client = HttpSpotifyOAuthClient(transport=_build_transport())

    async def run() -> None:
        token = await client.exchange_code(
            client_id="client-id",
            client_secret="client-secret",
            code="auth-code",
            redirect_uri="http://127.0.0.1:8000/callback",
        )
        profile = await client.fetch_profile(access_token=token.access_token)
        assert token.access_token == "access-token"
        assert token.refresh_token == "refresh-token"
        assert profile.id == "spotify-user-123"
        assert profile.display_name == "Bloom Listener"

    asyncio.run(run())


def test_refresh_access_token_preserves_refresh_token_when_missing() -> None:
    client = HttpSpotifyOAuthClient(transport=_build_transport())

    async def run() -> None:
        token = await client.refresh_access_token(
            client_id="client-id",
            client_secret="client-secret",
            refresh_token="refresh-token",
        )
        assert token.access_token == "refreshed-access-token"
        assert token.refresh_token == "refresh-token"

    asyncio.run(run())


def test_build_authorize_url_contains_required_params() -> None:
    client = HttpSpotifyOAuthClient()
    url = client.build_authorize_url(
        client_id="client-id",
        redirect_uri="http://127.0.0.1:8000/callback",
        scopes=["user-read-email"],
        state="secure-state",
    )

    assert "client_id=client-id" in url
    assert "state=secure-state" in url
    assert "response_type=code" in url
