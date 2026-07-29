"""Tests for Spotify playback service."""

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
from musicbloom.models.spotify_playback import SpotifyPlaybackStatus
from musicbloom.repositories.spotify_connection import SpotifyConnectionRepository
from musicbloom.security.token_encryption import TokenEncryptor
from musicbloom.services.spotify_auth import SpotifyAuthService
from musicbloom.services.spotify_playback import SpotifyPlaybackService
from musicbloom.services.spotify_playback_errors import (
    SpotifyInsufficientScopeError,
    SpotifyNoActiveDeviceError,
    SpotifyRateLimitedError,
)


def _spotify_settings(**overrides: object) -> Settings:
    base: dict[str, object] = {
        "secret_key": SecretStr("development-secret-key-for-tests!!"),
        "token_encryption_key": SecretStr("development-token-encryption-key"),
        "spotify_client_id": "test-client-id",
        "spotify_client_secret": SecretStr("test-client-secret"),
        "spotify_redirect_uri": "http://127.0.0.1:8000/api/v1/auth/spotify/callback",
    }
    base.update(overrides)
    return Settings(**base)


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


def _playback_transport(*, idle: bool = False) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v1/me/player/recently-played":
            return httpx.Response(200, json={"items": []})
        if request.url.path == "/v1/me/player" and request.method == "GET":
            if idle:
                return httpx.Response(204)
            return httpx.Response(200, json=_playback_state())
        if request.url.path.startswith("/v1/me/player/"):
            return httpx.Response(204)
        return httpx.Response(404)

    return httpx.MockTransport(handler)


@pytest.fixture
def playback_service(db_session: Session) -> SpotifyPlaybackService:
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
    auth_service = SpotifyAuthService(
        settings=_spotify_settings(),
        user_id=user.id,
        repository=SpotifyConnectionRepository(db_session),
        spotify_client=HttpSpotifyOAuthClient(
            transport=httpx.MockTransport(lambda _: httpx.Response(404)),
        ),
    )
    return SpotifyPlaybackService(
        auth_service=auth_service,
        playback_client=HttpSpotifyPlaybackClient(transport=_playback_transport()),
    )


def test_get_player_returns_connected_snapshot(
    playback_service: SpotifyPlaybackService,
) -> None:
    snapshot = asyncio.run(playback_service.get_player())

    assert snapshot.connected is True
    assert snapshot.status is SpotifyPlaybackStatus.PLAYING
    assert snapshot.track is not None
    assert snapshot.track.title == "Garden Echoes"
    assert snapshot.control_available is True


def test_get_player_idle_when_no_active_playback(db_session: Session) -> None:
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
    service = SpotifyPlaybackService(
        auth_service=SpotifyAuthService(
            settings=_spotify_settings(),
            user_id=user.id,
            repository=SpotifyConnectionRepository(db_session),
            spotify_client=HttpSpotifyOAuthClient(
                transport=httpx.MockTransport(lambda _: httpx.Response(404)),
            ),
        ),
        playback_client=HttpSpotifyPlaybackClient(
            transport=_playback_transport(idle=True),
        ),
    )

    snapshot = asyncio.run(service.get_player())

    assert snapshot.status is SpotifyPlaybackStatus.IDLE
    assert snapshot.track is None
    assert snapshot.message is not None


def test_play_requires_active_device(db_session: Session) -> None:
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
    service = SpotifyPlaybackService(
        auth_service=SpotifyAuthService(
            settings=_spotify_settings(),
            user_id=user.id,
            repository=SpotifyConnectionRepository(db_session),
            spotify_client=HttpSpotifyOAuthClient(
                transport=httpx.MockTransport(lambda _: httpx.Response(404)),
            ),
        ),
        playback_client=HttpSpotifyPlaybackClient(
            transport=_playback_transport(idle=True),
        ),
    )

    with pytest.raises(SpotifyNoActiveDeviceError):
        asyncio.run(service.play())


def test_playback_control_requires_scope(db_session: Session) -> None:
    user = get_demo_user(db_session)
    encryptor = TokenEncryptor(_spotify_settings().token_encryption_key)  # type: ignore[arg-type]
    SpotifyConnectionRepository(db_session).upsert_connection(
        user_id=user.id,
        spotify_user_id="spotify-user-123",
        display_name="Bloom Listener",
        encrypted_access_token=encryptor.encrypt("access-token"),
        encrypted_refresh_token=encryptor.encrypt("refresh-token"),
        token_expires_at=datetime.now(tz=UTC) + timedelta(hours=1),
        scopes="user-read-playback-state",
    )
    service = SpotifyPlaybackService(
        auth_service=SpotifyAuthService(
            settings=_spotify_settings(),
            user_id=user.id,
            repository=SpotifyConnectionRepository(db_session),
            spotify_client=HttpSpotifyOAuthClient(
                transport=httpx.MockTransport(lambda _: httpx.Response(404)),
            ),
        ),
        playback_client=HttpSpotifyPlaybackClient(transport=_playback_transport()),
    )

    with pytest.raises(SpotifyInsufficientScopeError):
        asyncio.run(service.pause())


def test_rate_limit_is_mapped(db_session: Session) -> None:
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

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, headers={"Retry-After": "30"})

    service = SpotifyPlaybackService(
        auth_service=SpotifyAuthService(
            settings=_spotify_settings(),
            user_id=user.id,
            repository=SpotifyConnectionRepository(db_session),
            spotify_client=HttpSpotifyOAuthClient(
                transport=httpx.MockTransport(lambda _: httpx.Response(404)),
            ),
        ),
        playback_client=HttpSpotifyPlaybackClient(transport=httpx.MockTransport(handler)),
    )

    with pytest.raises(SpotifyRateLimitedError):
        asyncio.run(service.get_player())
