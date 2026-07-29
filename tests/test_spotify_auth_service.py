"""Tests for Spotify auth service."""

import asyncio
from datetime import UTC, datetime, timedelta

import httpx
import pytest
from pydantic import SecretStr
from sqlalchemy.orm import Session

from musicbloom.config import Settings
from musicbloom.db.init import get_demo_user
from musicbloom.integrations.spotify.client import HttpSpotifyOAuthClient
from musicbloom.models.spotify import SpotifyConnectionStatusCode
from musicbloom.repositories.spotify_connection import SpotifyConnectionRepository
from musicbloom.security.oauth_state import (
    build_signed_oauth_state,
    generate_oauth_state,
)
from musicbloom.security.token_encryption import TokenEncryptor
from musicbloom.services.spotify_auth import SpotifyAuthService
from musicbloom.services.spotify_auth_errors import (
    AuthorizationDeniedError,
    OAuthStateMismatchError,
    SpotifyConnectionNotFoundError,
    SpotifyNotConfiguredError,
    SpotifyTokenError,
)


def _spotify_settings(**overrides: object) -> Settings:
    base: dict[str, object] = {
        "secret_key": SecretStr("development-secret-key-for-tests!!"),
        "token_encryption_key": SecretStr("development-token-encryption-key"),
        "spotify_client_id": "test-client-id",
        "spotify_client_secret": SecretStr("test-client-secret"),
        "spotify_redirect_uri": "http://127.0.0.1:8000/api/v1/auth/spotify/callback",
        "spotify_frontend_success_redirect": "http://localhost:5173/?spotify=connected",
        "spotify_frontend_failure_redirect": "http://localhost:5173/?spotify=error",
    }
    base.update(overrides)
    return Settings(**base)


def _mock_transport() -> httpx.MockTransport:
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
        return httpx.Response(404)

    return httpx.MockTransport(handler)


@pytest.fixture
def spotify_service(db_session: Session) -> SpotifyAuthService:
    user = get_demo_user(db_session)
    return SpotifyAuthService(
        settings=_spotify_settings(),
        user_id=user.id,
        repository=SpotifyConnectionRepository(db_session),
        spotify_client=HttpSpotifyOAuthClient(transport=_mock_transport()),
    )


def test_status_when_spotify_not_configured(db_session: Session) -> None:
    user = get_demo_user(db_session)
    service = SpotifyAuthService(
        settings=Settings(),
        user_id=user.id,
        repository=SpotifyConnectionRepository(db_session),
        spotify_client=HttpSpotifyOAuthClient(transport=_mock_transport()),
    )

    status = asyncio.run(service.get_status())

    assert status.configured is False
    assert status.status is SpotifyConnectionStatusCode.DISCONNECTED


def test_begin_login_requires_configuration(db_session: Session) -> None:
    user = get_demo_user(db_session)
    service = SpotifyAuthService(
        settings=Settings(),
        user_id=user.id,
        repository=SpotifyConnectionRepository(db_session),
        spotify_client=HttpSpotifyOAuthClient(transport=_mock_transport()),
    )

    with pytest.raises(SpotifyNotConfiguredError):
        service.begin_login()


def test_begin_login_returns_authorize_url(spotify_service: SpotifyAuthService) -> None:
    url, signed_state = spotify_service.begin_login()

    assert "client_id=test-client-id" in url
    assert signed_state


def test_complete_login_persists_encrypted_tokens(
    spotify_service: SpotifyAuthService,
    db_session: Session,
) -> None:
    user = get_demo_user(db_session)
    state = generate_oauth_state()
    signed_state = build_signed_oauth_state(
        state,
        _spotify_settings().secret_key,  # type: ignore[arg-type]
    )

    redirect_url = asyncio.run(
        spotify_service.complete_login(
            code="auth-code",
            state=state,
            signed_state_cookie=signed_state,
            error=None,
        ),
    )

    assert redirect_url.endswith("spotify=connected")
    record = SpotifyConnectionRepository(db_session).get_for_user(user.id)
    assert record is not None
    assert record.spotify_user_id == "spotify-user-123"
    assert "access-token" not in record.encrypted_access_token


def test_complete_login_rejects_state_mismatch(
    spotify_service: SpotifyAuthService,
) -> None:
    state = generate_oauth_state()
    signed_state = build_signed_oauth_state(
        state,
        _spotify_settings().secret_key,  # type: ignore[arg-type]
    )

    with pytest.raises(OAuthStateMismatchError):
        asyncio.run(
            spotify_service.complete_login(
                code="auth-code",
                state="different-state",
                signed_state_cookie=signed_state,
                error=None,
            ),
        )


def test_complete_login_handles_denied_authorization(
    spotify_service: SpotifyAuthService,
) -> None:
    with pytest.raises(AuthorizationDeniedError):
        asyncio.run(
            spotify_service.complete_login(
                code=None,
                state=None,
                signed_state_cookie=None,
                error="access_denied",
            ),
        )


def test_get_status_returns_connected_state(
    spotify_service: SpotifyAuthService,
) -> None:
    state = generate_oauth_state()
    signed_state = build_signed_oauth_state(
        state,
        _spotify_settings().secret_key,  # type: ignore[arg-type]
    )
    asyncio.run(
        spotify_service.complete_login(
            code="auth-code",
            state=state,
            signed_state_cookie=signed_state,
            error=None,
        ),
    )

    status = asyncio.run(spotify_service.get_status())

    assert status.status is SpotifyConnectionStatusCode.CONNECTED
    assert status.spotify_user_id == "spotify-user-123"
    assert status.display_name == "Bloom Listener"


def test_get_status_refreshes_expired_token(
    db_session: Session,
    spotify_service: SpotifyAuthService,
) -> None:
    user = get_demo_user(db_session)
    repo = SpotifyConnectionRepository(db_session)
    encryptor_secret = _spotify_settings().token_encryption_key
    from musicbloom.security.token_encryption import TokenEncryptor

    encryptor = TokenEncryptor(encryptor_secret)  # type: ignore[arg-type]
    repo.upsert_connection(
        user_id=user.id,
        spotify_user_id="spotify-user-123",
        display_name="Bloom Listener",
        encrypted_access_token=encryptor.encrypt("old-access-token"),
        encrypted_refresh_token=encryptor.encrypt("refresh-token"),
        token_expires_at=datetime.now(tz=UTC) - timedelta(minutes=5),
        scopes="user-read-email",
    )

    status = asyncio.run(spotify_service.get_status())

    assert status.status is SpotifyConnectionStatusCode.CONNECTED
    updated = repo.get_for_user(user.id)
    assert updated is not None
    assert encryptor.decrypt(updated.encrypted_access_token) == "refreshed-access-token"


def test_disconnect_requires_existing_connection(
    spotify_service: SpotifyAuthService,
) -> None:
    with pytest.raises(SpotifyConnectionNotFoundError):
        spotify_service.disconnect()


def test_get_valid_access_token_returns_decrypted_token(
    spotify_service: SpotifyAuthService,
) -> None:
    state = generate_oauth_state()
    signed_state = build_signed_oauth_state(
        state,
        _spotify_settings().secret_key,  # type: ignore[arg-type]
    )
    asyncio.run(
        spotify_service.complete_login(
            code="auth-code",
            state=state,
            signed_state_cookie=signed_state,
            error=None,
        ),
    )

    token = asyncio.run(spotify_service.get_valid_access_token())

    assert token == "access-token"


def test_get_valid_access_token_raises_when_connection_has_error(
    db_session: Session,
) -> None:
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
        scopes="user-read-email",
    )
    repo.mark_error(
        record=record,
        error_code="token_refresh_failed",
        error_message="Spotify access token refresh failed",
    )
    service = SpotifyAuthService(
        settings=_spotify_settings(),
        user_id=user.id,
        repository=repo,
        spotify_client=HttpSpotifyOAuthClient(
            transport=httpx.MockTransport(lambda _: httpx.Response(404)),
        ),
    )

    with pytest.raises(SpotifyTokenError):
        asyncio.run(service.get_valid_access_token())


def test_get_valid_access_token_raises_on_decrypt_failure(
    db_session: Session,
) -> None:
    user = get_demo_user(db_session)
    repo = SpotifyConnectionRepository(db_session)
    repo.upsert_connection(
        user_id=user.id,
        spotify_user_id="spotify-user-123",
        display_name="Bloom Listener",
        encrypted_access_token="invalid",
        encrypted_refresh_token="invalid",
        token_expires_at=datetime.now(tz=UTC) + timedelta(hours=1),
        scopes="user-read-email",
    )
    service = SpotifyAuthService(
        settings=_spotify_settings(),
        user_id=user.id,
        repository=repo,
        spotify_client=HttpSpotifyOAuthClient(
            transport=httpx.MockTransport(lambda _: httpx.Response(404)),
        ),
    )

    with pytest.raises(SpotifyTokenError):
        asyncio.run(service.get_valid_access_token())


def test_get_valid_access_token_raises_after_failed_refresh(
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
    service = SpotifyAuthService(
        settings=_spotify_settings(),
        user_id=user.id,
        repository=repo,
        spotify_client=HttpSpotifyOAuthClient(
            transport=httpx.MockTransport(
                lambda _: httpx.Response(500, json={"error": "server_error"}),
            ),
        ),
    )

    with pytest.raises(SpotifyTokenError):
        asyncio.run(service.get_valid_access_token())


def test_disconnect_removes_connection(
    spotify_service: SpotifyAuthService,
    db_session: Session,
) -> None:
    user = get_demo_user(db_session)
    state = generate_oauth_state()
    signed_state = build_signed_oauth_state(
        state,
        _spotify_settings().secret_key,  # type: ignore[arg-type]
    )
    asyncio.run(
        spotify_service.complete_login(
            code="auth-code",
            state=state,
            signed_state_cookie=signed_state,
            error=None,
        ),
    )

    result = spotify_service.disconnect()

    assert result.disconnected is True
    assert SpotifyConnectionRepository(db_session).get_for_user(user.id) is None
