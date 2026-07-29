"""Spotify OAuth authentication business logic."""

from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode, urlparse, urlunparse

import httpx
from pydantic import SecretStr

from musicbloom.config import Settings
from musicbloom.db.models.spotify_connection import SpotifyConnectionRecord
from musicbloom.integrations.spotify.client import SpotifyOAuthClient
from musicbloom.models.spotify import (
    SpotifyConnectionStatus,
    SpotifyConnectionStatusCode,
    SpotifyDisconnectResult,
)
from musicbloom.repositories.spotify_connection import SpotifyConnectionRepository
from musicbloom.security.oauth_state import (
    OAuthStateError,
    build_signed_oauth_state,
    generate_oauth_state,
    states_match,
    validate_signed_oauth_state,
)
from musicbloom.security.token_encryption import TokenEncryptionError, TokenEncryptor
from musicbloom.services.spotify_auth_errors import (
    AuthorizationDeniedError,
    OAuthStateMismatchError,
    SpotifyConnectionNotFoundError,
    SpotifyNotConfiguredError,
    SpotifyTokenError,
)


class SpotifyAuthService:
    """Service layer for Spotify account connection."""

    TOKEN_REFRESH_BUFFER = timedelta(minutes=2)

    def __init__(
        self,
        *,
        settings: Settings,
        user_id: int,
        repository: SpotifyConnectionRepository,
        spotify_client: SpotifyOAuthClient,
    ) -> None:
        self._settings = settings
        self._user_id = user_id
        self._repository = repository
        self._spotify_client = spotify_client

    def is_configured(self) -> bool:
        """Return whether Spotify OAuth is configured."""
        return self._settings.spotify_configured

    def begin_login(self) -> tuple[str, str]:
        """Return the Spotify authorization URL and signed OAuth state cookie value."""
        self._require_configured()
        oauth_secret = self._require_oauth_state_secret()
        state = generate_oauth_state()
        signed_state = build_signed_oauth_state(state, oauth_secret)
        authorize_url = self._spotify_client.build_authorize_url(
            client_id=self._required_client_id(),
            redirect_uri=self._required_redirect_uri(),
            scopes=self._settings.spotify_scopes,
            state=state,
        )
        return authorize_url, signed_state

    async def complete_login(
        self,
        *,
        code: str | None,
        state: str | None,
        signed_state_cookie: str | None,
        error: str | None,
    ) -> str:
        """Complete OAuth login and return the frontend redirect URL."""
        if error == "access_denied":
            raise AuthorizationDeniedError("Spotify authorization was denied")

        self._require_configured()
        oauth_secret = self._require_oauth_state_secret()
        if code is None or state is None or signed_state_cookie is None:
            raise OAuthStateMismatchError("Spotify OAuth callback is incomplete")

        try:
            expected_state = validate_signed_oauth_state(
                signed_state_cookie,
                oauth_secret,
            )
        except OAuthStateError as exc:
            raise OAuthStateMismatchError("Spotify OAuth state is invalid") from exc

        if not states_match(expected_state, state):
            raise OAuthStateMismatchError("Spotify OAuth state mismatch")

        encryptor = self._require_encryptor()
        try:
            token_response = await self._spotify_client.exchange_code(
                client_id=self._required_client_id(),
                client_secret=self._required_client_secret(),
                code=code,
                redirect_uri=self._required_redirect_uri(),
            )
            profile = await self._spotify_client.fetch_profile(
                access_token=token_response.access_token,
            )
        except httpx.HTTPError as exc:
            raise SpotifyTokenError("Spotify token exchange failed") from exc

        if not token_response.refresh_token:
            raise SpotifyTokenError("Spotify did not return a refresh token")

        self._repository.upsert_connection(
            user_id=self._user_id,
            spotify_user_id=profile.id,
            display_name=profile.display_name,
            encrypted_access_token=encryptor.encrypt(token_response.access_token),
            encrypted_refresh_token=encryptor.encrypt(token_response.refresh_token),
            token_expires_at=token_response.expires_at,
            scopes=token_response.scope or " ".join(self._settings.spotify_scopes),
        )
        return self._settings.spotify_frontend_success_redirect

    async def get_status(self) -> SpotifyConnectionStatus:
        """Return the current Spotify connection status."""
        if not self.is_configured():
            return SpotifyConnectionStatus(
                status=SpotifyConnectionStatusCode.DISCONNECTED,
                configured=False,
            )

        record = self._repository.get_for_user(self._user_id)
        if record is None:
            return SpotifyConnectionStatus(
                status=SpotifyConnectionStatusCode.DISCONNECTED,
                configured=True,
            )

        if record.last_error_code:
            return self._build_error_status(record)

        if self._token_needs_refresh(record):
            refreshed = await self._refresh_connection(record)
            if refreshed.last_error_code:
                return self._build_error_status(refreshed)

        return self._build_connected_status(record)

    def disconnect(self) -> SpotifyDisconnectResult:
        """Disconnect the current user's Spotify account."""
        removed = self._repository.delete_for_user(self._user_id)
        if not removed:
            raise SpotifyConnectionNotFoundError("No Spotify account is connected")
        return SpotifyDisconnectResult(disconnected=True)

    async def get_valid_access_token(self) -> str:
        """Return a valid access token for Spotify API calls."""
        self._require_configured()
        record = self._repository.get_for_user(self._user_id)
        if record is None:
            raise SpotifyConnectionNotFoundError("No Spotify account is connected")

        if record.last_error_code:
            raise SpotifyTokenError(
                record.last_error_message or "Spotify connection needs attention",
            )

        if self._token_needs_refresh(record):
            record = await self._refresh_connection(record)
            if record.last_error_code:
                raise SpotifyTokenError(
                    record.last_error_message or "Spotify access token refresh failed",
                )

        encryptor = self._require_encryptor()
        try:
            return encryptor.decrypt(record.encrypted_access_token)
        except TokenEncryptionError as exc:
            raise SpotifyTokenError("Unable to decrypt Spotify access token") from exc

    def failure_redirect(self, *, reason: str) -> str:
        """Return a frontend failure redirect URL with a safe reason code."""
        return self._append_query_param(
            self._settings.spotify_frontend_failure_redirect,
            {"reason": reason},
        )

    def _build_connected_status(
        self,
        record: SpotifyConnectionRecord,
    ) -> SpotifyConnectionStatus:
        return SpotifyConnectionStatus(
            status=SpotifyConnectionStatusCode.CONNECTED,
            configured=True,
            display_name=record.display_name,
            spotify_user_id=record.spotify_user_id,
            scopes=self._parse_scopes(record.scopes),
            expires_at=record.token_expires_at,
        )

    def _build_error_status(
        self,
        record: SpotifyConnectionRecord,
    ) -> SpotifyConnectionStatus:
        return SpotifyConnectionStatus(
            status=SpotifyConnectionStatusCode.ERROR,
            configured=True,
            display_name=record.display_name,
            spotify_user_id=record.spotify_user_id,
            scopes=self._parse_scopes(record.scopes),
            expires_at=record.token_expires_at,
            error_code=record.last_error_code,
            error_message=record.last_error_message,
        )

    async def _refresh_connection(
        self,
        record: SpotifyConnectionRecord,
    ) -> SpotifyConnectionRecord:
        encryptor = self._require_encryptor()
        try:
            refresh_token = encryptor.decrypt(record.encrypted_refresh_token)
            token_response = await self._spotify_client.refresh_access_token(
                client_id=self._required_client_id(),
                client_secret=self._required_client_secret(),
                refresh_token=refresh_token,
            )
        except (httpx.HTTPError, TokenEncryptionError):
            return self._repository.mark_error(
                record=record,
                error_code="token_refresh_failed",
                error_message="Spotify access token refresh failed",
            )

        return self._repository.update_tokens(
            record=record,
            encrypted_access_token=encryptor.encrypt(token_response.access_token),
            encrypted_refresh_token=encryptor.encrypt(
                token_response.refresh_token or refresh_token,
            ),
            token_expires_at=token_response.expires_at,
        )

    def _token_needs_refresh(self, record: SpotifyConnectionRecord) -> bool:
        expires_at = self._ensure_utc(record.token_expires_at)
        refresh_at = expires_at - self.TOKEN_REFRESH_BUFFER
        return datetime.now(tz=UTC) >= refresh_at

    def _ensure_utc(self, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)

    def _parse_scopes(self, scopes: str) -> list[str]:
        return [scope for scope in scopes.split() if scope]

    def _append_query_param(self, url: str, params: dict[str, str]) -> str:
        parsed = urlparse(url)
        existing: dict[str, str] = {}
        if parsed.query:
            for pair in parsed.query.split("&"):
                if not pair:
                    continue
                if "=" in pair:
                    key, value = pair.split("=", 1)
                else:
                    key, value = pair, ""
                existing[key] = value
        existing.update(params)
        query = urlencode(existing)
        return urlunparse(parsed._replace(query=query))

    def _require_configured(self) -> None:
        if not self.is_configured():
            raise SpotifyNotConfiguredError("Spotify OAuth is not configured")

    def _require_oauth_state_secret(self) -> SecretStr:
        secret = self._settings.resolved_oauth_state_secret
        if secret is None or not secret.get_secret_value().strip():
            raise SpotifyNotConfiguredError(
                "OAuth state signing requires secret_key or token_encryption_key",
            )
        return secret

    def _require_encryptor(self) -> TokenEncryptor:
        secret = self._settings.resolved_token_encryption_key
        if secret is None or not secret.get_secret_value().strip():
            raise SpotifyNotConfiguredError(
                "Token encryption requires token_encryption_key or secret_key",
            )
        return TokenEncryptor(secret)

    def _required_client_id(self) -> str:
        client_id = self._settings.spotify_client_id
        if client_id is None or not client_id.strip():
            raise SpotifyNotConfiguredError("Spotify client ID is not configured")
        return client_id.strip()

    def _required_client_secret(self) -> str:
        secret = self._settings.spotify_client_secret
        if secret is None or not secret.get_secret_value().strip():
            raise SpotifyNotConfiguredError("Spotify client secret is not configured")
        return secret.get_secret_value().strip()

    def _required_redirect_uri(self) -> str:
        redirect_uri = self._settings.spotify_redirect_uri
        if redirect_uri is None or not redirect_uri.strip():
            raise SpotifyNotConfiguredError("Spotify redirect URI is not configured")
        return redirect_uri.strip()
