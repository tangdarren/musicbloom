"""Spotify playback exception handlers."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from musicbloom.services.spotify_playback_errors import SpotifyPlaybackServiceError


def register_spotify_playback_exception_handlers(app: FastAPI) -> None:
    """Register HTTP handlers for Spotify playback service errors."""

    @app.exception_handler(SpotifyPlaybackServiceError)
    async def handle_spotify_playback_service_error(
        _request: Request,
        exc: SpotifyPlaybackServiceError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message},
        )
