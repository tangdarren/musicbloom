"""Listening event submission routes."""

from fastapi import APIRouter

from musicbloom.api.v1.schemas.progression import (
    ListeningEventRequest,
    ListeningEventResponse,
)
from musicbloom.dependencies import ProgressionServiceDep

router = APIRouter(prefix="/listening", tags=["listening"])


@router.post(
    "/events",
    response_model=ListeningEventResponse,
    summary="Submit a listening event",
    description=(
        "Report a listening event for validated progression rewards. "
        "Melody Points and experience are calculated server-side; "
        "client-supplied totals are ignored."
    ),
)
def submit_listening_event(
    request: ListeningEventRequest,
    progression_service: ProgressionServiceDep,
) -> ListeningEventResponse:
    """Process a listening event and return transparent award explanations."""
    return progression_service.submit_listening_event(
        track_id=request.track_id,
        event_type=request.event_type,
        position_ms=request.position_ms,
        idempotency_key=request.idempotency_key,
        occurred_at=request.occurred_at,
    )
