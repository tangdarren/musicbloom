"""Spotify authentication routes."""

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from musicbloom.api.v1.schemas.spotify_auth import (
    SpotifyConnectionStatusResponse,
    SpotifyDisconnectResponse,
)
from musicbloom.config import (
    OAUTH_STATE_COOKIE,
    OAUTH_STATE_MAX_AGE_SECONDS,
    Settings,
)
from musicbloom.dependencies import SettingsDep, SpotifyAuthServiceDep
from musicbloom.services.spotify_auth_errors import (
    AuthorizationDeniedError,
    OAuthStateMismatchError,
    SpotifyNotConfiguredError,
    SpotifyTokenError,
)

router = APIRouter(prefix="/auth/spotify", tags=["spotify-auth"])


def _set_oauth_state_cookie(
    response: RedirectResponse,
    settings: Settings,
    signed_state: str,
) -> None:
    response.set_cookie(
        OAUTH_STATE_COOKIE,
        signed_state,
        httponly=True,
        samesite="lax",
        max_age=OAUTH_STATE_MAX_AGE_SECONDS,
        secure=settings.environment == "production",
        path="/api/v1/auth/spotify",
    )


@router.get(
    "/login",
    summary="Begin Spotify OAuth login",
    description=(
        "Redirect the browser to Spotify authorization. Requires server-side "
        "Spotify credentials; demo mode continues to work when credentials are unset."
    ),
)
def spotify_login(
    settings: SettingsDep,
    spotify_auth_service: SpotifyAuthServiceDep,
) -> RedirectResponse:
    """Start the Spotify OAuth authorization-code flow."""
    if not spotify_auth_service.is_configured():
        return RedirectResponse(
            url=spotify_auth_service.failure_redirect(reason="not_configured"),
            status_code=302,
        )

    authorize_url, signed_state = spotify_auth_service.begin_login()
    response = RedirectResponse(url=authorize_url, status_code=302)
    _set_oauth_state_cookie(response, settings, signed_state)
    return response


@router.get(
    "/callback",
    summary="Handle Spotify OAuth callback",
    description="Complete Spotify OAuth and redirect back to the frontend.",
)
async def spotify_callback(
    request: Request,
    spotify_auth_service: SpotifyAuthServiceDep,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
) -> RedirectResponse:
    """Handle Spotify redirect after authorization."""
    signed_state = request.cookies.get(OAUTH_STATE_COOKIE)
    try:
        redirect_url = await spotify_auth_service.complete_login(
            code=code,
            state=state,
            signed_state_cookie=signed_state,
            error=error,
        )
    except AuthorizationDeniedError:
        redirect_url = spotify_auth_service.failure_redirect(reason="denied")
    except OAuthStateMismatchError:
        redirect_url = spotify_auth_service.failure_redirect(reason="state_mismatch")
    except SpotifyNotConfiguredError:
        redirect_url = spotify_auth_service.failure_redirect(reason="not_configured")
    except SpotifyTokenError:
        redirect_url = spotify_auth_service.failure_redirect(reason="token_error")

    response = RedirectResponse(url=redirect_url, status_code=302)
    response.delete_cookie(OAUTH_STATE_COOKIE, path="/api/v1/auth/spotify")
    return response


@router.get(
    "/status",
    response_model=SpotifyConnectionStatusResponse,
    summary="Get Spotify connection status",
    description="Return Spotify connection status without exposing token material.",
)
async def spotify_status(
    spotify_auth_service: SpotifyAuthServiceDep,
) -> SpotifyConnectionStatusResponse:
    """Return Spotify connection status for the current user."""
    return await spotify_auth_service.get_status()


@router.delete(
    "",
    response_model=SpotifyDisconnectResponse,
    summary="Disconnect Spotify account",
    description="Remove stored Spotify tokens for the current user.",
)
def spotify_disconnect(
    spotify_auth_service: SpotifyAuthServiceDep,
) -> SpotifyDisconnectResponse:
    """Disconnect the current user's Spotify account."""
    return spotify_auth_service.disconnect()
