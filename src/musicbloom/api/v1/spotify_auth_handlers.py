"""Spotify auth exception handlers."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from musicbloom.services.spotify_auth_errors import SpotifyAuthServiceError


def register_spotify_auth_exception_handlers(app: FastAPI) -> None:
    """Register HTTP handlers for Spotify auth service errors."""

    @app.exception_handler(SpotifyAuthServiceError)
    async def handle_spotify_auth_service_error(
        _request: Request,
        exc: SpotifyAuthServiceError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message},
        )
