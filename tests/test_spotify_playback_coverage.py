"""Additional Spotify playback coverage tests."""

import asyncio
from datetime import UTC, datetime, timedelta

import httpx
import pytest
from pydantic import SecretStr
from sqlalchemy.orm import Session

from musicbloom.config import Settings
from musicbloom.db.init import get_demo_user
from musicbloom.integrations.spotify.client import HttpSpotifyOAuthClient
from musicbloom.integrations.spotify.playback_client import HttpSpotifyPlaybackClient
from musicbloom.repositories.spotify_connection import SpotifyConnectionRepository
from musicbloom.security.token_encryption import TokenEncryptor
from musicbloom.services.spotify_auth import SpotifyAuthService
from musicbloom.services.spotify_auth_errors import SpotifyNotConfiguredError
from musicbloom.services.spotify_playback import (
    SpotifyPlaybackService,
    _parse_device,
    _parse_recently_played,
    _parse_track_item,
)
from musicbloom.services.spotify_playback_errors import (
    SpotifyInsufficientScopeError,
    SpotifyNoActiveDeviceError,
    SpotifyPlaybackApiError,
    SpotifyPlaybackNotConfiguredError,
    SpotifyPlaybackNotConnectedError,
    SpotifyRateLimitedError,
    SpotifyTokenUnavailableError,
)


def _spotify_settings() -> Settings:
    return Settings(
        secret_key=SecretStr("development-secret-key-for-tests!!"),
        token_encryption_key=SecretStr("development-token-encryption-key"),
        spotify_client_id="test-client-id",
        spotify_client_secret=SecretStr("test-client-secret"),
        spotify_redirect_uri="http://127.0.0.1:8000/api/v1/auth/spotify/callback",
    )


def _connected_service(
    db_session: Session,
    *,
    transport: httpx.MockTransport | None = None,
    playback_client: HttpSpotifyPlaybackClient | None = None,
    scopes: str = "user-read-playback-state user-modify-playback-state",
) -> SpotifyPlaybackService:
    user = get_demo_user(db_session)
    encryptor = TokenEncryptor(_spotify_settings().token_encryption_key)  # type: ignore[arg-type]
    SpotifyConnectionRepository(db_session).upsert_connection(
        user_id=user.id,
        spotify_user_id="spotify-user-123",
        display_name="Bloom Listener",
        encrypted_access_token=encryptor.encrypt("access-token"),
        encrypted_refresh_token=encryptor.encrypt("refresh-token"),
        token_expires_at=datetime.now(tz=UTC) + timedelta(hours=1),
        scopes=scopes,
    )
    client = playback_client or HttpSpotifyPlaybackClient(
        transport=transport or httpx.MockTransport(lambda _: httpx.Response(404)),
    )
    return SpotifyPlaybackService(
        auth_service=SpotifyAuthService(
            settings=_spotify_settings(),
            user_id=user.id,
            repository=SpotifyConnectionRepository(db_session),
            spotify_client=HttpSpotifyOAuthClient(
                transport=httpx.MockTransport(lambda _: httpx.Response(404)),
            ),
        ),
        playback_client=client,
    )


def test_get_player_when_not_configured(db_session: Session) -> None:
    service = SpotifyPlaybackService(
        auth_service=SpotifyAuthService(
            settings=Settings(),
            user_id=get_demo_user(db_session).id,
            repository=SpotifyConnectionRepository(db_session),
            spotify_client=HttpSpotifyOAuthClient(
                transport=httpx.MockTransport(lambda _: httpx.Response(404)),
            ),
        ),
        playback_client=HttpSpotifyPlaybackClient(
            transport=httpx.MockTransport(lambda _: httpx.Response(404)),
        ),
    )

    snapshot = asyncio.run(service.get_player())

    assert snapshot.configured is False
    assert snapshot.connected is False


def test_get_player_maps_403_to_scope_error(db_session: Session) -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(403)

    service = _connected_service(
        db_session,
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(SpotifyInsufficientScopeError):
        asyncio.run(service.get_player())


def test_seek_rejects_negative_position(db_session: Session) -> None:
    service = _connected_service(
        db_session,
        transport=httpx.MockTransport(lambda _: httpx.Response(204)),
    )

    with pytest.raises(SpotifyPlaybackApiError):
        asyncio.run(service.seek(-1))


def test_set_volume_rejects_invalid_level(db_session: Session) -> None:
    service = _connected_service(
        db_session,
        transport=httpx.MockTransport(lambda _: httpx.Response(204)),
    )

    with pytest.raises(SpotifyPlaybackApiError):
        asyncio.run(service.set_volume(1.5))


def test_playback_parsers_handle_invalid_payloads() -> None:
    assert _parse_device(None) is None
    assert _parse_track_item({"id": 1}) is None
    assert _parse_recently_played({"items": "invalid"}) == []


def test_get_player_not_connected(db_session: Session) -> None:
    service = SpotifyPlaybackService(
        auth_service=SpotifyAuthService(
            settings=_spotify_settings(),
            user_id=get_demo_user(db_session).id,
            repository=SpotifyConnectionRepository(db_session),
            spotify_client=HttpSpotifyOAuthClient(
                transport=httpx.MockTransport(lambda _: httpx.Response(404)),
            ),
        ),
        playback_client=HttpSpotifyPlaybackClient(
            transport=httpx.MockTransport(lambda _: httpx.Response(404)),
        ),
    )

    snapshot = asyncio.run(service.get_player())

    assert snapshot.connected is False


def test_control_context_maps_token_error(db_session: Session) -> None:
    user = get_demo_user(db_session)
    repo = SpotifyConnectionRepository(db_session)
    encryptor = TokenEncryptor(_spotify_settings().token_encryption_key)  # type: ignore[arg-type]
    record = repo.upsert_connection(
        user_id=user.id,
        spotify_user_id="spotify-user-123",
        display_name="Bloom Listener",
        encrypted_access_token=encryptor.encrypt("access-token"),
        encrypted_refresh_token=encryptor.encrypt("refresh-token"),
        token_expires_at=datetime.now(tz=UTC) + timedelta(hours=1),
        scopes="user-read-playback-state user-modify-playback-state",
    )
    repo.mark_error(
        record=record,
        error_code="token_refresh_failed",
        error_message="Spotify access token refresh failed",
    )
    service = SpotifyPlaybackService(
        auth_service=SpotifyAuthService(
            settings=_spotify_settings(),
            user_id=user.id,
            repository=repo,
            spotify_client=HttpSpotifyOAuthClient(
                transport=httpx.MockTransport(lambda _: httpx.Response(404)),
            ),
        ),
        playback_client=HttpSpotifyPlaybackClient(
            transport=httpx.MockTransport(lambda _: httpx.Response(204)),
        ),
    )

    with pytest.raises(SpotifyTokenUnavailableError):
        asyncio.run(service.pause())


def test_not_configured_error_when_auth_missing(db_session: Session) -> None:
    service = SpotifyPlaybackService(
        auth_service=SpotifyAuthService(
            settings=Settings(),
            user_id=get_demo_user(db_session).id,
            repository=SpotifyConnectionRepository(db_session),
            spotify_client=HttpSpotifyOAuthClient(
                transport=httpx.MockTransport(lambda _: httpx.Response(404)),
            ),
        ),
        playback_client=HttpSpotifyPlaybackClient(
            transport=httpx.MockTransport(lambda _: httpx.Response(204)),
        ),
    )

    with pytest.raises(SpotifyPlaybackNotConfiguredError):
        asyncio.run(service.play())


def _playback_state() -> dict[str, object]:
    return {
        "device": {
            "id": "device-123",
            "is_active": True,
            "name": "Bloom Laptop",
            "type": "Computer",
            "volume_percent": 55,
        },
        "shuffle_state": True,
        "repeat_state": "context",
        "progress_ms": 42_000,
        "is_playing": False,
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


def _interactive_transport(
    *,
    playback_status: int = 200,
    control_status: int = 204,
) -> httpx.MockTransport:
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
        if request.url.path == "/v1/me/player" and request.method == "GET":
            if playback_status == 204:
                return httpx.Response(204)
            return httpx.Response(playback_status, json=_playback_state())
        if request.url.path.startswith("/v1/me/player/"):
            return httpx.Response(control_status)
        return httpx.Response(404)

    return httpx.MockTransport(handler)


def test_playback_control_methods_return_snapshot(db_session: Session) -> None:
    service = _connected_service(
        db_session,
        transport=_interactive_transport(),
    )

    snapshot = asyncio.run(service.play())
    assert snapshot.status.value == "paused"

    snapshot = asyncio.run(service.pause())
    assert snapshot.connected is True

    snapshot = asyncio.run(service.next_track())
    assert snapshot.track is not None

    snapshot = asyncio.run(service.previous_track())
    assert snapshot.track is not None

    snapshot = asyncio.run(service.seek(15_000))
    assert snapshot.progress_ms == 42_000

    snapshot = asyncio.run(service.set_volume(0.4))
    assert snapshot.device is not None


@pytest.mark.parametrize(
    ("status_code", "expected_error"),
    [
        (401, SpotifyTokenUnavailableError),
        (404, SpotifyNoActiveDeviceError),
        (429, SpotifyRateLimitedError),
        (502, SpotifyPlaybackApiError),
    ],
)
def test_get_player_maps_http_errors(
    db_session: Session,
    status_code: int,
    expected_error: type[Exception],
) -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        headers = {"Retry-After": "10"} if status_code == 429 else None
        return httpx.Response(status_code, headers=headers)

    service = _connected_service(
        db_session,
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(expected_error):
        asyncio.run(service.get_player())


def test_get_player_maps_token_error_from_auth(db_session: Session) -> None:
    user = get_demo_user(db_session)
    repo = SpotifyConnectionRepository(db_session)
    encryptor = TokenEncryptor(_spotify_settings().token_encryption_key)  # type: ignore[arg-type]
    record = repo.upsert_connection(
        user_id=user.id,
        spotify_user_id="spotify-user-123",
        display_name="Bloom Listener",
        encrypted_access_token=encryptor.encrypt("access-token"),
        encrypted_refresh_token=encryptor.encrypt("refresh-token"),
        token_expires_at=datetime.now(tz=UTC) + timedelta(hours=1),
        scopes="user-read-playback-state user-modify-playback-state",
    )
    repo.mark_error(
        record=record,
        error_code="token_refresh_failed",
        error_message="Spotify access token refresh failed",
    )
    service = SpotifyPlaybackService(
        auth_service=SpotifyAuthService(
            settings=_spotify_settings(),
            user_id=user.id,
            repository=repo,
            spotify_client=HttpSpotifyOAuthClient(
                transport=httpx.MockTransport(lambda _: httpx.Response(404)),
            ),
        ),
        playback_client=HttpSpotifyPlaybackClient(
            transport=_interactive_transport(),
        ),
    )

    snapshot = asyncio.run(service.get_player())
    assert snapshot.connected is False
    assert snapshot.message is not None


def test_playback_parsers_cover_edge_cases() -> None:
    assert _parse_device({"name": "Speaker", "type": "Speaker", "is_active": True})
    track = _parse_track_item(
        {
            "id": "track-123",
            "name": "Song",
            "duration_ms": 1000,
            "artists": [],
            "album": {"name": "Album", "images": []},
        },
    )
    assert track is not None
    assert track.artist_name == "Unknown artist"

    recent = _parse_recently_played(
        {
            "items": [
                {
                    "played_at": "2026-01-15T12:00:00.000Z",
                    "track": {
                        "id": "track-123",
                        "name": "Song",
                        "duration_ms": 1000,
                        "artists": [{"name": "Artist"}],
                    },
                },
                {"played_at": "bad", "track": None},
            ],
        },
    )
    assert len(recent) == 1


def test_require_control_context_without_device_id(db_session: Session) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v1/me/player/recently-played":
            return httpx.Response(200, json={"items": []})
        if request.url.path == "/v1/me/player" and request.method == "GET":
            payload = _playback_state()
            device = dict(payload["device"])  # type: ignore[index]
            device.pop("id")
            payload["device"] = device
            return httpx.Response(200, json=payload)
        if request.url.path.startswith("/v1/me/player/"):
            return httpx.Response(204)
        return httpx.Response(404)

    service = _connected_service(
        db_session,
        transport=httpx.MockTransport(handler),
    )

    snapshot = asyncio.run(service.play())
    assert snapshot.connected is True


def test_get_player_raises_on_generic_http_error(db_session: Session) -> None:
    class BrokenTransport(httpx.AsyncBaseTransport):
        async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("network down", request=request)

    service = _connected_service(
        db_session,
        playback_client=HttpSpotifyPlaybackClient(transport=BrokenTransport()),
    )

    with pytest.raises(SpotifyPlaybackApiError):
        asyncio.run(service.get_player())


def test_control_methods_raise_on_http_error(db_session: Session) -> None:
    class BrokenTransport(httpx.AsyncBaseTransport):
        async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
            if request.url.path == "/v1/me/player" and request.method == "GET":
                return httpx.Response(200, json=_playback_state())
            raise httpx.ConnectError("network down", request=request)

    service = _connected_service(
        db_session,
        playback_client=HttpSpotifyPlaybackClient(transport=BrokenTransport()),
    )

    with pytest.raises(SpotifyPlaybackApiError):
        asyncio.run(service.pause())


@pytest.mark.parametrize(
    "method_name",
    ["play", "pause", "next_track", "previous_track", "seek", "set_volume"],
)
def test_control_methods_raise_on_transport_errors(
    db_session: Session,
    method_name: str,
) -> None:
    class BrokenTransport(httpx.AsyncBaseTransport):
        async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
            if request.url.path == "/v1/me/player" and request.method == "GET":
                return httpx.Response(200, json=_playback_state())
            raise httpx.ConnectError("network down", request=request)

    service = _connected_service(
        db_session,
        playback_client=HttpSpotifyPlaybackClient(transport=BrokenTransport()),
    )
    method = getattr(service, method_name)

    with pytest.raises(SpotifyPlaybackApiError):
        if method_name == "seek":
            asyncio.run(method(1_000))
        elif method_name == "set_volume":
            asyncio.run(method(0.5))
        else:
            asyncio.run(method())


def test_map_http_error_covers_service_unavailable(db_session: Session) -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(503)

    service = _connected_service(
        db_session,
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(SpotifyPlaybackApiError):
        asyncio.run(service.get_player())


def test_playback_parsers_handle_invalid_structures() -> None:
    assert _parse_device({"name": 1, "type": "Speaker"}) is None
    assert _parse_track_item({"id": "x", "name": 1}) is None
    assert _parse_recently_played({"items": "bad"}) == []


def test_get_player_without_control_scope_still_returns_metadata(
    db_session: Session,
) -> None:
    service = _connected_service(
        db_session,
        transport=_interactive_transport(),
        scopes="user-read-playback-state",
    )

    snapshot = asyncio.run(service.get_player())

    assert snapshot.connected is True
    assert snapshot.control_available is False


def test_get_player_raises_not_configured_when_auth_inconsistent(
    db_session: Session,
) -> None:
    from unittest.mock import AsyncMock, MagicMock

    auth_service = MagicMock()
    auth_service.is_configured.return_value = True
    auth_service.get_valid_access_token = AsyncMock(
        side_effect=SpotifyNotConfiguredError("Spotify OAuth is not configured"),
    )
    service = SpotifyPlaybackService(
        auth_service=auth_service,
        playback_client=HttpSpotifyPlaybackClient(
            transport=httpx.MockTransport(lambda _: httpx.Response(404)),
        ),
    )

    with pytest.raises(SpotifyPlaybackNotConfiguredError):
        asyncio.run(service.get_player())


def test_control_methods_raise_on_http_status_errors(db_session: Session) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v1/me/player" and request.method == "GET":
            return httpx.Response(200, json=_playback_state())
        return httpx.Response(500)

    service = _connected_service(
        db_session,
        transport=httpx.MockTransport(handler),
    )

    for call in (
        lambda: service.play(),
        lambda: service.pause(),
        lambda: service.next_track(),
        lambda: service.previous_track(),
        lambda: service.seek(1_000),
        lambda: service.set_volume(0.5),
    ):
        with pytest.raises(SpotifyPlaybackApiError):
            asyncio.run(call())


def test_require_control_context_maps_status_errors(db_session: Session) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v1/me/player" and request.method == "GET":
            return httpx.Response(404)
        return httpx.Response(404)

    service = _connected_service(
        db_session,
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(SpotifyNoActiveDeviceError):
        asyncio.run(service.play())


def test_map_http_error_default_case(db_session: Session) -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(500)

    service = _connected_service(
        db_session,
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(SpotifyPlaybackApiError, match="request failed"):
        asyncio.run(service.get_player())


def test_playback_parsers_cover_optional_album_fields() -> None:
    track = _parse_track_item(
        {
            "id": "track-123",
            "name": "Song",
            "duration_ms": 1000,
            "artists": [{"name": "Artist"}],
        },
    )
    assert track is not None
    assert track.album_title is None

    recent = _parse_recently_played(
        {
            "items": [
                {
                    "played_at": "2026-01-15T12:00:00",
                    "track": {
                        "id": "track-123",
                        "name": "Song",
                        "duration_ms": 1000,
                        "artists": [{"name": "Artist"}],
                    },
                },
            ],
        },
    )
    assert len(recent) == 1


def test_get_valid_access_token_refreshes_before_returning(
    db_session: Session,
) -> None:
    user = get_demo_user(db_session)
    repo = SpotifyConnectionRepository(db_session)
    encryptor = TokenEncryptor(_spotify_settings().token_encryption_key)  # type: ignore[arg-type]
    repo.upsert_connection(
        user_id=user.id,
        spotify_user_id="spotify-user-123",
        display_name="Bloom Listener",
        encrypted_access_token=encryptor.encrypt("old-access-token"),
        encrypted_refresh_token=encryptor.encrypt("refresh-token"),
        token_expires_at=datetime.now(tz=UTC) - timedelta(minutes=5),
        scopes="user-read-email",
    )

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/token":
            return httpx.Response(
                200,
                json={
                    "access_token": "refreshed-access-token",
                    "expires_in": 3600,
                    "token_type": "Bearer",
                    "scope": "user-read-email",
                },
            )
        return httpx.Response(404)

    service = SpotifyAuthService(
        settings=_spotify_settings(),
        user_id=user.id,
        repository=repo,
        spotify_client=HttpSpotifyOAuthClient(transport=httpx.MockTransport(handler)),
    )

    token = asyncio.run(service.get_valid_access_token())

    assert token == "refreshed-access-token"


def test_play_without_connection_raises_not_connected(db_session: Session) -> None:
    service = SpotifyPlaybackService(
        auth_service=SpotifyAuthService(
            settings=_spotify_settings(),
            user_id=get_demo_user(db_session).id,
            repository=SpotifyConnectionRepository(db_session),
            spotify_client=HttpSpotifyOAuthClient(
                transport=httpx.MockTransport(lambda _: httpx.Response(404)),
            ),
        ),
        playback_client=HttpSpotifyPlaybackClient(
            transport=httpx.MockTransport(lambda _: httpx.Response(404)),
        ),
    )

    with pytest.raises(SpotifyPlaybackNotConnectedError):
        asyncio.run(service.play())


def test_require_control_context_raises_on_network_error(db_session: Session) -> None:
    class BrokenTransport(httpx.AsyncBaseTransport):
        async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("network down", request=request)

    service = _connected_service(
        db_session,
        playback_client=HttpSpotifyPlaybackClient(transport=BrokenTransport()),
    )

    with pytest.raises(SpotifyPlaybackApiError):
        asyncio.run(service.play())


def test_require_control_context_raises_when_playback_is_idle(
    db_session: Session,
) -> None:
    service = _connected_service(
        db_session,
        transport=_interactive_transport(playback_status=204),
    )

    with pytest.raises(SpotifyNoActiveDeviceError):
        asyncio.run(service.play())


def test_recently_played_ignored_when_request_fails(db_session: Session) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v1/me/player/recently-played":
            return httpx.Response(500)
        if request.url.path == "/v1/me/player":
            return httpx.Response(200, json=_playback_state())
        return httpx.Response(404)

    service = _connected_service(
        db_session,
        transport=httpx.MockTransport(handler),
    )

    snapshot = asyncio.run(service.get_player())

    assert snapshot.recently_played == []


def test_playback_parsers_skip_invalid_recent_items() -> None:
    assert _parse_recently_played({"items": ["bad-item"]}) == []
    track = _parse_track_item(
        {
            "id": "track-123",
            "name": "Song",
            "duration_ms": 1000,
            "uri": "spotify:track:track-123",
            "artists": [{"name": "Artist"}],
            "album": {"name": "Album"},
        },
    )
    assert track is not None
    assert track.spotify_uri == "spotify:track:track-123"


def test_playback_parsers_cover_artist_album_and_artwork() -> None:
    track = _parse_track_item(
        {
            "id": "track-123",
            "name": "Song",
            "duration_ms": 1000,
            "artists": [{"name": "Featured Artist"}],
            "album": {
                "name": "Album Title",
                "images": [{"url": "https://example.com/cover.jpg"}],
            },
        },
    )
    assert track is not None
    assert track.artist_name == "Featured Artist"
    assert track.album_title == "Album Title"
    assert track.artwork_url == "https://example.com/cover.jpg"

    track_without_artwork = _parse_track_item(
        {
            "id": "track-789",
            "name": "No Art",
            "duration_ms": 1000,
            "artists": [{"name": "Artist"}],
            "album": {
                "name": 123,
                "images": [{"url": "https://example.com/cover.jpg"}],
            },
        },
    )
    assert track_without_artwork is not None
    assert track_without_artwork.album_title is None
    assert track_without_artwork.artwork_url == "https://example.com/cover.jpg"

    track_without_image_dict = _parse_track_item(
        {
            "id": "track-790",
            "name": "No Art",
            "duration_ms": 1000,
            "artists": [{"name": "Artist"}],
            "album": {
                "name": "Album",
                "images": ["not-a-dict"],
            },
        },
    )
    assert track_without_image_dict is not None
    assert track_without_image_dict.artwork_url is None

    track_without_artist_name = _parse_track_item(
        {
            "id": "track-456",
            "name": "Other Song",
            "duration_ms": 2000,
            "artists": [{"id": "artist-1"}],
        },
    )
    assert track_without_artist_name is not None
    assert track_without_artist_name.artist_name == "Unknown artist"
