"""Tests for Spotify playback HTTP client."""

import asyncio

import httpx
import pytest

from musicbloom.integrations.spotify.playback_client import HttpSpotifyPlaybackClient


def _playback_state() -> dict[str, object]:
    return {
        "device": {
            "id": "device-123",
            "is_active": True,
            "is_private_session": False,
            "is_restricted": False,
            "name": "Bloom Laptop",
            "type": "Computer",
            "volume_percent": 55,
        },
        "shuffle_state": False,
        "repeat_state": "off",
        "timestamp": 1_700_000_000_000,
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


def _build_transport() -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v1/me/player/recently-played":
            return httpx.Response(
                200,
                json={
                    "items": [
                        {
                            "played_at": "2026-01-15T12:00:00Z",
                            "track": _playback_state()["item"],
                        },
                    ],
                },
            )
        if request.url.path == "/v1/me/player":
            if request.method == "GET":
                return httpx.Response(200, json=_playback_state())
            return httpx.Response(204)
        if request.url.path.startswith("/v1/me/player/"):
            return httpx.Response(204)
        return httpx.Response(404)

    return httpx.MockTransport(handler)


def test_get_playback_state_returns_payload() -> None:
    client = HttpSpotifyPlaybackClient(transport=_build_transport())

    async def run() -> None:
        payload = await client.get_playback_state(access_token="token")
        assert payload is not None
        assert payload["is_playing"] is True

    asyncio.run(run())


def test_get_playback_state_returns_none_for_204() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(204)

    client = HttpSpotifyPlaybackClient(transport=httpx.MockTransport(handler))

    async def run() -> None:
        payload = await client.get_playback_state(access_token="token")
        assert payload is None

    asyncio.run(run())


def test_player_commands_accept_success_statuses() -> None:
    client = HttpSpotifyPlaybackClient(transport=_build_transport())

    async def run() -> None:
        await client.start_playback(access_token="token")
        await client.pause_playback(access_token="token")
        await client.skip_to_next(access_token="token")
        await client.skip_to_previous(access_token="token")
        await client.seek(access_token="token", position_ms=15_000)
        await client.set_volume(access_token="token", volume_percent=40)

    asyncio.run(run())


def test_get_playback_state_rejects_non_object_payload() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=["not-an-object"])

    client = HttpSpotifyPlaybackClient(transport=httpx.MockTransport(handler))

    async def run() -> None:
        with pytest.raises(TypeError, match="playback response"):
            await client.get_playback_state(access_token="token")

    asyncio.run(run())


def test_get_recently_played_rejects_non_object_payload() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=["not-an-object"])

    client = HttpSpotifyPlaybackClient(transport=httpx.MockTransport(handler))

    async def run() -> None:
        with pytest.raises(TypeError, match="recently played"):
            await client.get_recently_played(access_token="token")

    asyncio.run(run())
