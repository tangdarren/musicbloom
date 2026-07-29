"""Garden exception handlers."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from musicbloom.services.garden_errors import GardenServiceError


def register_garden_exception_handlers(app: FastAPI) -> None:
    """Register HTTP handlers for garden service errors."""

    @app.exception_handler(GardenServiceError)
    async def handle_garden_service_error(
        _request: Request,
        exc: GardenServiceError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message},
        )
