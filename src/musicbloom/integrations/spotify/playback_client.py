"""Spotify Web API playback client."""

from typing import Any, Protocol

import httpx

from musicbloom.config import SPOTIFY_API_BASE_URL


class SpotifyPlaybackClient(Protocol):
    """Protocol for Spotify playback Web API interactions."""

    async def get_playback_state(self, *, access_token: str) -> dict[str, Any] | None:
        """Return playback state or None when nothing is playing."""

    async def get_recently_played(
        self,
        *,
        access_token: str,
        limit: int = 5,
    ) -> dict[str, Any]:
        """Return recently played tracks."""

    async def start_playback(
        self,
        *,
        access_token: str,
        device_id: str | None = None,
    ) -> None:
        """Resume or start playback on the active device."""

    async def pause_playback(
        self,
        *,
        access_token: str,
        device_id: str | None = None,
    ) -> None:
        """Pause playback on the active device."""

    async def skip_to_next(
        self,
        *,
        access_token: str,
        device_id: str | None = None,
    ) -> None:
        """Skip to the next track."""

    async def skip_to_previous(
        self,
        *,
        access_token: str,
        device_id: str | None = None,
    ) -> None:
        """Skip to the previous track."""

    async def seek(
        self,
        *,
        access_token: str,
        position_ms: int,
        device_id: str | None = None,
    ) -> None:
        """Seek within the active track."""

    async def set_volume(
        self,
        *,
        access_token: str,
        volume_percent: int,
        device_id: str | None = None,
    ) -> None:
        """Set playback volume on the active device."""


class HttpSpotifyPlaybackClient:
    """HTTP-backed Spotify playback client."""

    def __init__(self, transport: httpx.AsyncBaseTransport | None = None) -> None:
        self._transport = transport

    async def get_playback_state(self, *, access_token: str) -> dict[str, Any] | None:
        async with httpx.AsyncClient(transport=self._transport) as client:
            response = await client.get(
                f"{SPOTIFY_API_BASE_URL}/me/player",
                headers=_auth_headers(access_token),
            )
            if response.status_code == 204:
                return None
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, dict):
                msg = "Spotify playback response was not an object"
                raise TypeError(msg)
            return payload

    async def get_recently_played(
        self,
        *,
        access_token: str,
        limit: int = 5,
    ) -> dict[str, Any]:
        async with httpx.AsyncClient(transport=self._transport) as client:
            response = await client.get(
                f"{SPOTIFY_API_BASE_URL}/me/player/recently-played",
                params={"limit": limit},
                headers=_auth_headers(access_token),
            )
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, dict):
                msg = "Spotify recently played response was not an object"
                raise TypeError(msg)
            return payload

    async def start_playback(
        self,
        *,
        access_token: str,
        device_id: str | None = None,
    ) -> None:
        await self._send_player_command(
            access_token=access_token,
            method="PUT",
            path="/me/player/play",
            device_id=device_id,
        )

    async def pause_playback(
        self,
        *,
        access_token: str,
        device_id: str | None = None,
    ) -> None:
        await self._send_player_command(
            access_token=access_token,
            method="PUT",
            path="/me/player/pause",
            device_id=device_id,
        )

    async def skip_to_next(
        self,
        *,
        access_token: str,
        device_id: str | None = None,
    ) -> None:
        await self._send_player_command(
            access_token=access_token,
            method="POST",
            path="/me/player/next",
            device_id=device_id,
        )

    async def skip_to_previous(
        self,
        *,
        access_token: str,
        device_id: str | None = None,
    ) -> None:
        await self._send_player_command(
            access_token=access_token,
            method="POST",
            path="/me/player/previous",
            device_id=device_id,
        )

    async def seek(
        self,
        *,
        access_token: str,
        position_ms: int,
        device_id: str | None = None,
    ) -> None:
        await self._send_player_command(
            access_token=access_token,
            method="PUT",
            path="/me/player/seek",
            device_id=device_id,
            params={"position_ms": position_ms},
        )

    async def set_volume(
        self,
        *,
        access_token: str,
        volume_percent: int,
        device_id: str | None = None,
    ) -> None:
        await self._send_player_command(
            access_token=access_token,
            method="PUT",
            path="/me/player/volume",
            device_id=device_id,
            params={"volume_percent": volume_percent},
        )

    async def _send_player_command(
        self,
        *,
        access_token: str,
        method: str,
        path: str,
        device_id: str | None,
        params: dict[str, int] | None = None,
    ) -> None:
        query: dict[str, str | int] = dict(params or {})
        if device_id:
            query["device_id"] = device_id
        async with httpx.AsyncClient(transport=self._transport) as client:
            response = await client.request(
                method,
                f"{SPOTIFY_API_BASE_URL}{path}",
                params=query or None,
                headers=_auth_headers(access_token),
            )
            if response.status_code in {200, 202, 204}:
                return
            response.raise_for_status()


def _auth_headers(access_token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
    }
