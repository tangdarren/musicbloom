"""Player session exception handlers."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from musicbloom.services.player_errors import PlayerServiceError


def register_player_exception_handlers(app: FastAPI) -> None:
    """Register HTTP handlers for player service errors."""

    @app.exception_handler(PlayerServiceError)
    async def handle_player_service_error(
        _request: Request,
        exc: PlayerServiceError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message},
        )
