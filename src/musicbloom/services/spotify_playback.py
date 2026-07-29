"""Spotify playback business logic."""

from datetime import UTC, datetime
from typing import Any

import httpx

from musicbloom.integrations.spotify.playback_client import SpotifyPlaybackClient
from musicbloom.models.spotify_playback import (
    SpotifyPlaybackStatus,
    SpotifyPlayerDevice,
    SpotifyPlayerSnapshot,
    SpotifyPlayerTrack,
    SpotifyRecentTrack,
)
from musicbloom.services.spotify_auth import SpotifyAuthService
from musicbloom.services.spotify_auth_errors import (
    SpotifyConnectionNotFoundError,
    SpotifyNotConfiguredError,
    SpotifyTokenError,
)
from musicbloom.services.spotify_playback_errors import (
    SpotifyInsufficientScopeError,
    SpotifyNoActiveDeviceError,
    SpotifyPlaybackApiError,
    SpotifyPlaybackNotConfiguredError,
    SpotifyPlaybackNotConnectedError,
    SpotifyPlaybackServiceError,
    SpotifyRateLimitedError,
    SpotifyTokenUnavailableError,
)

PLAYBACK_CONTROL_SCOPE = "user-modify-playback-state"
READ_PLAYBACK_SCOPE = "user-read-playback-state"


class SpotifyPlaybackService:
    """Service layer for Spotify playback metadata and control."""

    def __init__(
        self,
        *,
        auth_service: SpotifyAuthService,
        playback_client: SpotifyPlaybackClient,
    ) -> None:
        self._auth_service = auth_service
        self._playback_client = playback_client

    async def get_player(self) -> SpotifyPlayerSnapshot:
        """Return normalized Spotify playback state."""
        if not self._auth_service.is_configured():
            return self._idle_snapshot(
                configured=False,
                connected=False,
                message="Spotify OAuth is not configured on the server.",
                control_available=False,
                control_unavailable_reason=(
                    "Connect Spotify in server settings to enable playback metadata."
                ),
            )

        try:
            access_token = await self._auth_service.get_valid_access_token()
        except SpotifyNotConfiguredError as exc:
            raise SpotifyPlaybackNotConfiguredError(str(exc)) from exc
        except SpotifyConnectionNotFoundError as exc:
            return self._idle_snapshot(
                configured=True,
                connected=False,
                message="Connect your Spotify account to view playback metadata.",
                control_available=False,
                control_unavailable_reason=str(exc),
            )
        except SpotifyTokenError as exc:
            return self._idle_snapshot(
                configured=True,
                connected=False,
                message=str(exc),
                control_available=False,
                control_unavailable_reason=str(exc),
            )

        scopes = await self._resolve_scopes()
        control_available, control_reason = self._control_availability(scopes)

        try:
            state = await self._playback_client.get_playback_state(
                access_token=access_token,
            )
            recently_played = await self._safe_recently_played(access_token)
        except httpx.HTTPStatusError as exc:
            raise self._map_http_error(exc) from exc
        except httpx.HTTPError as exc:
            raise SpotifyPlaybackApiError("Spotify playback request failed") from exc

        if state is None:
            return self._idle_snapshot(
                configured=True,
                connected=True,
                message=(
                    "No active Spotify playback. Start playing on a Spotify device "
                    "to see live metadata here."
                ),
                control_available=control_available,
                control_unavailable_reason=control_reason,
                recently_played=recently_played,
            )

        return self._build_snapshot(
            state=state,
            recently_played=recently_played,
            control_available=control_available,
            control_unavailable_reason=control_reason,
        )

    async def play(self) -> SpotifyPlayerSnapshot:
        """Resume or start Spotify playback."""
        access_token, device_id = await self._require_control_context()
        try:
            await self._playback_client.start_playback(
                access_token=access_token,
                device_id=device_id,
            )
        except httpx.HTTPStatusError as exc:
            raise self._map_http_error(exc) from exc
        except httpx.HTTPError as exc:
            raise SpotifyPlaybackApiError("Spotify play request failed") from exc
        return await self.get_player()

    async def pause(self) -> SpotifyPlayerSnapshot:
        """Pause Spotify playback."""
        access_token, device_id = await self._require_control_context()
        try:
            await self._playback_client.pause_playback(
                access_token=access_token,
                device_id=device_id,
            )
        except httpx.HTTPStatusError as exc:
            raise self._map_http_error(exc) from exc
        except httpx.HTTPError as exc:
            raise SpotifyPlaybackApiError("Spotify pause request failed") from exc
        return await self.get_player()

    async def next_track(self) -> SpotifyPlayerSnapshot:
        """Skip to the next Spotify track."""
        access_token, device_id = await self._require_control_context()
        try:
            await self._playback_client.skip_to_next(
                access_token=access_token,
                device_id=device_id,
            )
        except httpx.HTTPStatusError as exc:
            raise self._map_http_error(exc) from exc
        except httpx.HTTPError as exc:
            raise SpotifyPlaybackApiError("Spotify next request failed") from exc
        return await self.get_player()

    async def previous_track(self) -> SpotifyPlayerSnapshot:
        """Skip to the previous Spotify track."""
        access_token, device_id = await self._require_control_context()
        try:
            await self._playback_client.skip_to_previous(
                access_token=access_token,
                device_id=device_id,
            )
        except httpx.HTTPStatusError as exc:
            raise self._map_http_error(exc) from exc
        except httpx.HTTPError as exc:
            raise SpotifyPlaybackApiError("Spotify previous request failed") from exc
        return await self.get_player()

    async def seek(self, position_ms: int) -> SpotifyPlayerSnapshot:
        """Seek within the active Spotify track."""
        if position_ms < 0:
            raise SpotifyPlaybackApiError("Seek position must be non-negative")
        access_token, device_id = await self._require_control_context()
        try:
            await self._playback_client.seek(
                access_token=access_token,
                position_ms=position_ms,
                device_id=device_id,
            )
        except httpx.HTTPStatusError as exc:
            raise self._map_http_error(exc) from exc
        except httpx.HTTPError as exc:
            raise SpotifyPlaybackApiError("Spotify seek request failed") from exc
        return await self.get_player()

    async def set_volume(self, level: float) -> SpotifyPlayerSnapshot:
        """Set Spotify playback volume using a normalized 0.0-1.0 level."""
        if level < 0.0 or level > 1.0:
            raise SpotifyPlaybackApiError("Volume level must be between 0.0 and 1.0")
        volume_percent = round(level * 100)
        access_token, device_id = await self._require_control_context()
        try:
            await self._playback_client.set_volume(
                access_token=access_token,
                volume_percent=volume_percent,
                device_id=device_id,
            )
        except httpx.HTTPStatusError as exc:
            raise self._map_http_error(exc) from exc
        except httpx.HTTPError as exc:
            raise SpotifyPlaybackApiError("Spotify volume request failed") from exc
        return await self.get_player()

    async def _require_control_context(self) -> tuple[str, str | None]:
        try:
            access_token = await self._auth_service.get_valid_access_token()
        except SpotifyNotConfiguredError as exc:
            raise SpotifyPlaybackNotConfiguredError(str(exc)) from exc
        except SpotifyConnectionNotFoundError as exc:
            raise SpotifyPlaybackNotConnectedError(str(exc)) from exc
        except SpotifyTokenError as exc:
            raise SpotifyTokenUnavailableError(str(exc)) from exc

        self._ensure_control_scope(await self._resolve_scopes())

        try:
            state = await self._playback_client.get_playback_state(
                access_token=access_token,
            )
        except httpx.HTTPStatusError as exc:
            raise self._map_http_error(exc) from exc
        except httpx.HTTPError as exc:
            raise SpotifyPlaybackApiError("Spotify playback request failed") from exc

        if state is None:
            raise SpotifyNoActiveDeviceError(
                "No active Spotify device found. Open Spotify on a phone, desktop, "
                "or web player and start playback before using controls.",
            )

        device = state.get("device")
        device_id = None
        if isinstance(device, dict) and device.get("id"):
            device_id = str(device["id"])
        return access_token, device_id

    async def _safe_recently_played(
        self,
        access_token: str,
    ) -> list[SpotifyRecentTrack]:
        try:
            payload = await self._playback_client.get_recently_played(
                access_token=access_token,
                limit=5,
            )
        except httpx.HTTPError:
            return []
        return _parse_recently_played(payload)

    async def _resolve_scopes(self) -> list[str]:
        status = await self._auth_service.get_status()
        return status.scopes

    def _control_availability(
        self,
        scopes: list[str],
    ) -> tuple[bool, str | None]:
        if PLAYBACK_CONTROL_SCOPE in scopes:
            return True, None
        return (
            False,
            (
                "Reconnect Spotify with playback-control scopes to use "
                "play, pause, and skip."
            ),
        )

    def _ensure_control_scope(self, scopes: list[str]) -> None:
        if PLAYBACK_CONTROL_SCOPE not in scopes:
            raise SpotifyInsufficientScopeError(
                "This Spotify connection is missing playback-control permissions. "
                "Disconnect and reconnect your account to grant them.",
            )

    def _build_snapshot(
        self,
        *,
        state: dict[str, Any],
        recently_played: list[SpotifyRecentTrack],
        control_available: bool,
        control_unavailable_reason: str | None,
    ) -> SpotifyPlayerSnapshot:
        is_playing = bool(state.get("is_playing"))
        status = (
            SpotifyPlaybackStatus.PLAYING
            if is_playing
            else SpotifyPlaybackStatus.PAUSED
        )
        progress_ms = state.get("progress_ms")
        track = _parse_track_item(state.get("item"))
        device = _parse_device(state.get("device"))

        return SpotifyPlayerSnapshot(
            status=status,
            configured=True,
            connected=True,
            is_playing=is_playing,
            progress_ms=int(progress_ms) if progress_ms is not None else None,
            track=track,
            device=device,
            shuffle=bool(state["shuffle_state"]) if "shuffle_state" in state else None,
            repeat_mode=(
                str(state["repeat_state"]) if state.get("repeat_state") else None
            ),
            recently_played=recently_played,
            message=None,
            control_available=control_available,
            control_unavailable_reason=control_unavailable_reason,
        )

    def _idle_snapshot(
        self,
        *,
        configured: bool,
        connected: bool,
        message: str,
        control_available: bool,
        control_unavailable_reason: str | None,
        recently_played: list[SpotifyRecentTrack] | None = None,
    ) -> SpotifyPlayerSnapshot:
        return SpotifyPlayerSnapshot(
            status=SpotifyPlaybackStatus.IDLE,
            configured=configured,
            connected=connected,
            is_playing=False,
            progress_ms=None,
            track=None,
            device=None,
            shuffle=None,
            repeat_mode=None,
            recently_played=recently_played or [],
            message=message,
            control_available=control_available,
            control_unavailable_reason=control_unavailable_reason,
        )

    def _map_http_error(
        self,
        exc: httpx.HTTPStatusError,
    ) -> SpotifyPlaybackServiceError:
        status_code = exc.response.status_code
        if status_code == 401:
            return SpotifyTokenUnavailableError(
                "Spotify access token is invalid or expired. Reconnect your account.",
            )
        if status_code == 403:
            return SpotifyInsufficientScopeError(
                "Spotify rejected the request because playback permissions "
                "are missing.",
            )
        if status_code == 404:
            return SpotifyNoActiveDeviceError(
                "No active Spotify device found. Open Spotify on a device "
                "and try again.",
            )
        if status_code == 429:
            retry_after = exc.response.headers.get("Retry-After")
            suffix = f" Try again in {retry_after} seconds." if retry_after else ""
            return SpotifyRateLimitedError(
                f"Spotify rate limit reached.{suffix}",
            )
        if status_code in {502, 503}:
            return SpotifyPlaybackApiError(
                "Spotify playback service is temporarily unavailable.",
            )
        return SpotifyPlaybackApiError("Spotify playback request failed.")


def _parse_device(payload: object) -> SpotifyPlayerDevice | None:
    if not isinstance(payload, dict):
        return None
    name = payload.get("name")
    device_type = payload.get("type")
    if not isinstance(name, str) or not isinstance(device_type, str):
        return None
    volume = payload.get("volume_percent")
    return SpotifyPlayerDevice(
        id=str(payload["id"]) if payload.get("id") else None,
        name=name,
        type=device_type,
        is_active=bool(payload.get("is_active")),
        volume_percent=int(volume) if volume is not None else None,
    )


def _parse_track_item(payload: object) -> SpotifyPlayerTrack | None:
    if not isinstance(payload, dict):
        return None
    track_id = payload.get("id")
    title = payload.get("name")
    if not isinstance(track_id, str) or not isinstance(title, str):
        return None

    artists = payload.get("artists")
    artist_name = "Unknown artist"
    if isinstance(artists, list) and artists:
        first = artists[0]
        if isinstance(first, dict) and isinstance(first.get("name"), str):
            artist_name = first["name"]

    album_title = None
    artwork_url = None
    album = payload.get("album")
    if isinstance(album, dict):
        if isinstance(album.get("name"), str):
            album_title = album["name"]
        images = album.get("images")
        if isinstance(images, list) and images:
            first_image = images[0]
            if isinstance(first_image, dict):
                image_url = first_image.get("url")
            else:
                image_url = None
            if isinstance(image_url, str):
                artwork_url = image_url

    duration_ms = int(payload.get("duration_ms") or 0)
    uri = payload.get("uri")
    return SpotifyPlayerTrack(
        track_id=track_id,
        title=title,
        artist_name=artist_name,
        album_title=album_title,
        duration_ms=duration_ms,
        artwork_url=artwork_url,
        spotify_uri=str(uri) if uri else None,
    )


def _parse_recently_played(payload: dict[str, Any]) -> list[SpotifyRecentTrack]:
    items = payload.get("items")
    if not isinstance(items, list):
        return []

    recent: list[SpotifyRecentTrack] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        played_at_raw = item.get("played_at")
        track_payload = item.get("track")
        track = _parse_track_item(track_payload)
        if track is None or not isinstance(played_at_raw, str):
            continue
        played_at = datetime.fromisoformat(played_at_raw.replace("Z", "+00:00"))
        if played_at.tzinfo is None:
            played_at = played_at.replace(tzinfo=UTC)
        recent.append(SpotifyRecentTrack(track=track, played_at=played_at))
    return recent
