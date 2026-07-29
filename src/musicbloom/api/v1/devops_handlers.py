"""Azure DevOps exception handlers."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from musicbloom.services.devops_errors import DevOpsServiceError


def register_devops_exception_handlers(app: FastAPI) -> None:
    """Register HTTP handlers for Azure DevOps service errors."""

    @app.exception_handler(DevOpsServiceError)
    async def handle_devops_service_error(
        _request: Request,
        exc: DevOpsServiceError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message},
        )
