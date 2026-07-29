"""Spotify OAuth HTTP client types and implementations."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Protocol
from urllib.parse import urlencode

import httpx

from musicbloom.config import (
    SPOTIFY_AUTHORIZE_URL,
    SPOTIFY_PROFILE_URL,
    SPOTIFY_TOKEN_URL,
)


@dataclass(frozen=True, slots=True)
class SpotifyTokenResponse:
    """Token payload returned by Spotify."""

    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str
    scope: str

    @property
    def expires_at(self) -> datetime:
        """Return the UTC expiration timestamp for the access token."""
        return datetime.now(tz=UTC) + timedelta(seconds=self.expires_in)


@dataclass(frozen=True, slots=True)
class SpotifyProfileResponse:
    """Minimal Spotify profile payload."""

    id: str
    display_name: str | None


class SpotifyOAuthClient(Protocol):
    """Protocol for Spotify OAuth API interactions."""

    def build_authorize_url(
        self,
        *,
        client_id: str,
        redirect_uri: str,
        scopes: list[str],
        state: str,
    ) -> str:
        """Build the Spotify authorization URL."""

    async def exchange_code(
        self,
        *,
        client_id: str,
        client_secret: str,
        code: str,
        redirect_uri: str,
    ) -> SpotifyTokenResponse:
        """Exchange an authorization code for tokens."""

    async def refresh_access_token(
        self,
        *,
        client_id: str,
        client_secret: str,
        refresh_token: str,
    ) -> SpotifyTokenResponse:
        """Refresh an access token."""

    async def fetch_profile(self, *, access_token: str) -> SpotifyProfileResponse:
        """Fetch the current Spotify user profile."""


class HttpSpotifyOAuthClient:
    """HTTP-backed Spotify OAuth client."""

    def __init__(self, transport: httpx.AsyncBaseTransport | None = None) -> None:
        self._transport = transport

    def build_authorize_url(
        self,
        *,
        client_id: str,
        redirect_uri: str,
        scopes: list[str],
        state: str,
    ) -> str:
        params = {
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": " ".join(scopes),
            "state": state,
            "show_dialog": "false",
        }
        return f"{SPOTIFY_AUTHORIZE_URL}?{urlencode(params)}"

    async def exchange_code(
        self,
        *,
        client_id: str,
        client_secret: str,
        code: str,
        redirect_uri: str,
    ) -> SpotifyTokenResponse:
        async with httpx.AsyncClient(transport=self._transport) as client:
            response = await client.post(
                SPOTIFY_TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": redirect_uri,
                },
                auth=(client_id, client_secret),
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()
            payload = response.json()
        return _parse_token_response(payload)

    async def refresh_access_token(
        self,
        *,
        client_id: str,
        client_secret: str,
        refresh_token: str,
    ) -> SpotifyTokenResponse:
        async with httpx.AsyncClient(transport=self._transport) as client:
            response = await client.post(
                SPOTIFY_TOKEN_URL,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                },
                auth=(client_id, client_secret),
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()
            payload = response.json()
        token = _parse_token_response(payload)
        if not payload.get("refresh_token"):
            return SpotifyTokenResponse(
                access_token=token.access_token,
                refresh_token=refresh_token,
                expires_in=token.expires_in,
                token_type=token.token_type,
                scope=token.scope,
            )
        return token

    async def fetch_profile(self, *, access_token: str) -> SpotifyProfileResponse:
        async with httpx.AsyncClient(transport=self._transport) as client:
            response = await client.get(
                SPOTIFY_PROFILE_URL,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json",
                },
            )
            response.raise_for_status()
            payload = response.json()
        return SpotifyProfileResponse(
            id=str(payload["id"]),
            display_name=payload.get("display_name"),
        )


def _parse_token_response(payload: dict[str, object]) -> SpotifyTokenResponse:
    access_token = str(payload["access_token"])
    refresh_token = str(payload.get("refresh_token") or "")
    expires_in = int(str(payload["expires_in"]))
    token_type = str(payload.get("token_type") or "Bearer")
    scope = str(payload.get("scope") or "")
    return SpotifyTokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in,
        token_type=token_type,
        scope=scope,
    )
