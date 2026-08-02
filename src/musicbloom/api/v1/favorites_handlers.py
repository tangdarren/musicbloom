"""Favorites exception handlers."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from musicbloom.services.favorites_errors import FavoritesServiceError


def register_favorites_exception_handlers(app: FastAPI) -> None:
    """Register HTTP handlers for favorites service errors."""

    @app.exception_handler(FavoritesServiceError)
    async def handle_favorites_service_error(
        _request: Request,
        exc: FavoritesServiceError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message},
        )
