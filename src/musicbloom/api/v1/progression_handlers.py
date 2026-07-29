"""Progression exception handlers."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from musicbloom.services.progression_errors import ProgressionServiceError


def register_progression_exception_handlers(app: FastAPI) -> None:
    """Register HTTP handlers for progression service errors."""

    @app.exception_handler(ProgressionServiceError)
    async def handle_progression_service_error(
        _request: Request,
        exc: ProgressionServiceError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message},
        )
