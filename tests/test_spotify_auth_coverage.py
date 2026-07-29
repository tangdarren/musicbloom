"""Additional Spotify auth coverage tests."""

import asyncio
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import httpx
import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy.orm import Session

from musicbloom.config import Settings
from musicbloom.db.init import get_demo_user
from musicbloom.integrations.spotify.client import (
    HttpSpotifyOAuthClient,
    SpotifyTokenResponse,
)
from musicbloom.models.spotify import SpotifyConnectionStatusCode
from musicbloom.repositories.spotify_connection import SpotifyConnectionRepository
from musicbloom.security.oauth_state import (
    build_signed_oauth_state,
    generate_oauth_state,
)
from musicbloom.security.token_encryption import TokenEncryptor
from musicbloom.services.spotify_auth import SpotifyAuthService
from musicbloom.services.spotify_auth_errors import (
    OAuthStateMismatchError,
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
            return httpx.Response(500, json={"error": "server_error"})
        return httpx.Response(404)

    return httpx.MockTransport(handler)


def _success_transport(*, include_refresh_token: bool = True) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/token":
            body = request.content.decode()
            payload: dict[str, object] = {
                "access_token": "access-token",
                "expires_in": 3600,
                "token_type": "Bearer",
                "scope": "user-read-email",
            }
            if "grant_type=authorization_code" in body and include_refresh_token:
                payload["refresh_token"] = "refresh-token"
            if "grant_type=refresh_token" in body:
                payload["access_token"] = "refreshed-access-token"
            return httpx.Response(200, json=payload)
        if request.url.path == "/v1/me":
            return httpx.Response(
                200,
                json={"id": "spotify-user-123", "display_name": "Bloom Listener"},
            )
        return httpx.Response(404)

    return httpx.MockTransport(handler)


@pytest.fixture
def configured_spotify_client(test_app) -> None:
    from musicbloom.dependencies import get_settings, get_spotify_oauth_client

    get_settings.cache_clear()
    test_app.dependency_overrides[get_settings] = lambda: _spotify_settings()
    test_app.dependency_overrides[get_spotify_oauth_client] = (
        lambda: HttpSpotifyOAuthClient(transport=_success_transport())
    )
    yield
    test_app.dependency_overrides.pop(get_settings, None)
    test_app.dependency_overrides.pop(get_spotify_oauth_client, None)
    get_settings.cache_clear()


@pytest.fixture
def failing_spotify_client(test_app) -> None:
    from musicbloom.dependencies import get_settings, get_spotify_oauth_client

    get_settings.cache_clear()
    test_app.dependency_overrides[get_settings] = lambda: _spotify_settings()
    test_app.dependency_overrides[get_spotify_oauth_client] = (
        lambda: HttpSpotifyOAuthClient(transport=_mock_transport())
    )
    yield
    test_app.dependency_overrides.pop(get_settings, None)
    test_app.dependency_overrides.pop(get_spotify_oauth_client, None)
    get_settings.cache_clear()


@pytest.fixture
def failing_spotify_service(db_session: Session) -> SpotifyAuthService:
    user = get_demo_user(db_session)
    return SpotifyAuthService(
        settings=_spotify_settings(),
        user_id=user.id,
        repository=SpotifyConnectionRepository(db_session),
        spotify_client=HttpSpotifyOAuthClient(transport=_mock_transport()),
    )


def test_refresh_failure_marks_connection_error(
    db_session: Session,
    failing_spotify_service: SpotifyAuthService,
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

    status = asyncio.run(failing_spotify_service.get_status())

    assert status.status is SpotifyConnectionStatusCode.ERROR
    assert status.error_code == "token_refresh_failed"


def test_complete_login_raises_on_token_exchange_failure(
    failing_spotify_service: SpotifyAuthService,
) -> None:
    state = generate_oauth_state()
    signed_state = build_signed_oauth_state(
        state,
        _spotify_settings().secret_key,  # type: ignore[arg-type]
    )

    with pytest.raises(SpotifyTokenError):
        asyncio.run(
            failing_spotify_service.complete_login(
                code="auth-code",
                state=state,
                signed_state_cookie=signed_state,
                error=None,
            ),
        )


def test_complete_login_rejects_incomplete_callback(
    failing_spotify_service: SpotifyAuthService,
) -> None:
    with pytest.raises(OAuthStateMismatchError):
        asyncio.run(
            failing_spotify_service.complete_login(
                code=None,
                state="state",
                signed_state_cookie="cookie",
                error=None,
            ),
        )


def test_complete_login_rejects_invalid_signed_state(
    failing_spotify_service: SpotifyAuthService,
) -> None:
    with pytest.raises(OAuthStateMismatchError):
        asyncio.run(
            failing_spotify_service.complete_login(
                code="auth-code",
                state="state",
                signed_state_cookie="invalid.state.signature",
                error=None,
            ),
        )


def test_complete_login_requires_refresh_token(db_session: Session) -> None:
    user = get_demo_user(db_session)
    service = SpotifyAuthService(
        settings=_spotify_settings(),
        user_id=user.id,
        repository=SpotifyConnectionRepository(db_session),
        spotify_client=HttpSpotifyOAuthClient(
            transport=_success_transport(include_refresh_token=False),
        ),
    )
    state = generate_oauth_state()
    signed_state = build_signed_oauth_state(
        state,
        _spotify_settings().secret_key,  # type: ignore[arg-type]
    )

    with pytest.raises(SpotifyTokenError, match="refresh token"):
        asyncio.run(
            service.complete_login(
                code="auth-code",
                state=state,
                signed_state_cookie=signed_state,
                error=None,
            ),
        )


def test_get_status_returns_error_when_connection_has_error(
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
        error_code="token_revoked",
        error_message="Spotify access token was revoked",
    )
    service = SpotifyAuthService(
        settings=_spotify_settings(),
        user_id=user.id,
        repository=repo,
        spotify_client=HttpSpotifyOAuthClient(transport=_success_transport()),
    )

    status = asyncio.run(service.get_status())

    assert status.status is SpotifyConnectionStatusCode.ERROR
    assert status.error_code == "token_revoked"
    assert status.error_message == "Spotify access token was revoked"


def test_get_status_returns_error_after_failed_refresh(
    db_session: Session,
    failing_spotify_service: SpotifyAuthService,
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

    status = asyncio.run(failing_spotify_service.get_status())

    assert status.status is SpotifyConnectionStatusCode.ERROR


def test_failure_redirect_without_existing_query(db_session: Session) -> None:
    user = get_demo_user(db_session)
    service = SpotifyAuthService(
        settings=_spotify_settings(
            spotify_frontend_failure_redirect="http://localhost:5173/spotify-error",
        ),
        user_id=user.id,
        repository=SpotifyConnectionRepository(db_session),
        spotify_client=MagicMock(),
    )

    url = service.failure_redirect(reason="denied")

    assert url == "http://localhost:5173/spotify-error?reason=denied"


def test_failure_redirect_appends_reason_query_param(
    db_session: Session,
) -> None:
    user = get_demo_user(db_session)
    service = SpotifyAuthService(
        settings=_spotify_settings(
            spotify_frontend_failure_redirect="http://localhost:5173/?spotify=error&foo=bar",
        ),
        user_id=user.id,
        repository=SpotifyConnectionRepository(db_session),
        spotify_client=HttpSpotifyOAuthClient(transport=_success_transport()),
    )

    url = service.failure_redirect(reason="denied")

    assert "reason=denied" in url
    assert "foo=bar" in url


def test_require_helpers_raise_when_unconfigured(db_session: Session) -> None:
    user = get_demo_user(db_session)
    base = SpotifyAuthService(
        settings=Settings(),
        user_id=user.id,
        repository=SpotifyConnectionRepository(db_session),
        spotify_client=HttpSpotifyOAuthClient(transport=_success_transport()),
    )

    with pytest.raises(SpotifyNotConfiguredError):
        base._require_oauth_state_secret()

    with pytest.raises(SpotifyNotConfiguredError):
        base._require_encryptor()

    partial = SpotifyAuthService(
        settings=Settings(
            secret_key=SecretStr("development-secret-key-for-tests!!"),
            token_encryption_key=SecretStr("development-token-encryption-key"),
        ),
        user_id=user.id,
        repository=SpotifyConnectionRepository(db_session),
        spotify_client=HttpSpotifyOAuthClient(transport=_success_transport()),
    )

    with pytest.raises(SpotifyNotConfiguredError):
        partial._required_client_id()

    with pytest.raises(SpotifyNotConfiguredError):
        partial._required_client_secret()

    with pytest.raises(SpotifyNotConfiguredError):
        partial._required_redirect_uri()


def test_upsert_connection_updates_existing_record(db_session: Session) -> None:
    user = get_demo_user(db_session)
    repo = SpotifyConnectionRepository(db_session)
    encryptor = TokenEncryptor(_spotify_settings().token_encryption_key)  # type: ignore[arg-type]
    expires_at = datetime.now(tz=UTC) + timedelta(hours=1)

    repo.upsert_connection(
        user_id=user.id,
        spotify_user_id="spotify-user-123",
        display_name="First Name",
        encrypted_access_token=encryptor.encrypt("access-token"),
        encrypted_refresh_token=encryptor.encrypt("refresh-token"),
        token_expires_at=expires_at,
        scopes="user-read-email",
    )
    updated = repo.upsert_connection(
        user_id=user.id,
        spotify_user_id="spotify-user-456",
        display_name="Updated Name",
        encrypted_access_token=encryptor.encrypt("new-access-token"),
        encrypted_refresh_token=encryptor.encrypt("new-refresh-token"),
        token_expires_at=expires_at + timedelta(hours=1),
        scopes="user-read-email user-read-private",
    )

    assert updated.spotify_user_id == "spotify-user-456"
    assert updated.display_name == "Updated Name"
    assert updated.last_error_code is None


def test_refresh_connection_updates_tokens(db_session: Session) -> None:
    user = get_demo_user(db_session)
    repo = SpotifyConnectionRepository(db_session)
    encryptor = TokenEncryptor(_spotify_settings().token_encryption_key)  # type: ignore[arg-type]
    record = repo.upsert_connection(
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
        spotify_client=HttpSpotifyOAuthClient(transport=_success_transport()),
    )

    refreshed = asyncio.run(service._refresh_connection(record))

    assert refreshed.last_error_code is None
    assert (
        encryptor.decrypt(refreshed.encrypted_access_token) == "refreshed-access-token"
    )


def test_refresh_connection_handles_encryption_error(db_session: Session) -> None:
    user = get_demo_user(db_session)
    repo = SpotifyConnectionRepository(db_session)
    record = repo.upsert_connection(
        user_id=user.id,
        spotify_user_id="spotify-user-123",
        display_name="Bloom Listener",
        encrypted_access_token="invalid",
        encrypted_refresh_token="invalid",
        token_expires_at=datetime.now(tz=UTC) - timedelta(minutes=5),
        scopes="user-read-email",
    )
    service = SpotifyAuthService(
        settings=_spotify_settings(),
        user_id=user.id,
        repository=repo,
        spotify_client=HttpSpotifyOAuthClient(transport=_success_transport()),
    )

    refreshed = asyncio.run(service._refresh_connection(record))

    assert refreshed.last_error_code == "token_refresh_failed"


def test_spotify_callback_state_mismatch_redirect(
    client: TestClient,
    configured_spotify_client: None,
) -> None:
    response = client.get(
        "/api/v1/auth/spotify/callback?code=auth-code&state=wrong-state",
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert "reason=state_mismatch" in response.headers["location"]


def test_spotify_callback_token_error_redirect(
    client: TestClient,
    failing_spotify_client: None,
) -> None:
    from musicbloom.config import OAUTH_STATE_COOKIE

    state = generate_oauth_state()
    signed_state = build_signed_oauth_state(
        state,
        _spotify_settings().secret_key,  # type: ignore[arg-type]
    )
    client.cookies.set(OAUTH_STATE_COOKIE, signed_state)

    response = client.get(
        f"/api/v1/auth/spotify/callback?code=auth-code&state={state}",
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert "reason=token_error" in response.headers["location"]


def test_mock_spotify_client_refresh_returns_new_refresh_token() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "access_token": "new-access",
                "refresh_token": "new-refresh",
                "expires_in": 3600,
                "token_type": "Bearer",
                "scope": "user-read-email",
            },
        )

    client = HttpSpotifyOAuthClient(transport=httpx.MockTransport(handler))

    async def run() -> SpotifyTokenResponse:
        return await client.refresh_access_token(
            client_id="client-id",
            client_secret="client-secret",
            refresh_token="old-refresh",
        )

    token = asyncio.run(run())
    assert token.refresh_token == "new-refresh"


def test_mock_spotify_client_http_error_raises() -> None:
    client = HttpSpotifyOAuthClient(transport=_mock_transport())

    async def run() -> None:
        await client.exchange_code(
            client_id="client-id",
            client_secret="client-secret",
            code="auth-code",
            redirect_uri="http://127.0.0.1:8000/callback",
        )

    with pytest.raises(httpx.HTTPStatusError):
        asyncio.run(run())


def test_parse_scopes_skips_empty_segments(db_session: Session) -> None:
    user = get_demo_user(db_session)
    service = SpotifyAuthService(
        settings=_spotify_settings(),
        user_id=user.id,
        repository=SpotifyConnectionRepository(db_session),
        spotify_client=MagicMock(),
    )

    assert service._parse_scopes("  user-read-email   user-read-private  ") == [
        "user-read-email",
        "user-read-private",
    ]


def test_ensure_utc_converts_aware_datetime(db_session: Session) -> None:
    from zoneinfo import ZoneInfo

    user = get_demo_user(db_session)
    service = SpotifyAuthService(
        settings=_spotify_settings(),
        user_id=user.id,
        repository=SpotifyConnectionRepository(db_session),
        spotify_client=MagicMock(),
    )

    aware = datetime(2026, 1, 1, 12, 0, tzinfo=ZoneInfo("America/Los_Angeles"))
    assert service._ensure_utc(aware).tzinfo == UTC


def test_append_query_param_handles_bare_and_empty_pairs(db_session: Session) -> None:
    user = get_demo_user(db_session)
    service = SpotifyAuthService(
        settings=_spotify_settings(),
        user_id=user.id,
        repository=SpotifyConnectionRepository(db_session),
        spotify_client=MagicMock(),
    )

    url = service._append_query_param(
        "http://localhost:5173/?foo=bar&&flag&reason=old",
        {"reason": "denied"},
    )

    assert "foo=bar" in url
    assert "flag=" in url
    assert "reason=denied" in url
