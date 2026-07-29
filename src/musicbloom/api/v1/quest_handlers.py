"""Quest and achievement exception handlers."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from musicbloom.services.quest_errors import QuestAchievementServiceError


def register_quest_exception_handlers(app: FastAPI) -> None:
    """Register HTTP handlers for quest and achievement service errors."""

    @app.exception_handler(QuestAchievementServiceError)
    async def handle_quest_service_error(
        _request: Request,
        exc: QuestAchievementServiceError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message},
        )
