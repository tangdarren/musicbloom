"""Player session control routes."""

from typing import Annotated

from fastapi import APIRouter, Depends

from musicbloom.api.v1.schemas.player import (
    PlayerSessionResponse,
    PlayRequest,
    QueueTrackRequest,
    RepeatRequest,
    SeekRequest,
    ShuffleRequest,
    VolumeRequest,
)
from musicbloom.dependencies import get_player_service
from musicbloom.services.player import PlayerService

router = APIRouter(prefix="/player", tags=["player"])


@router.get(
    "",
    response_model=PlayerSessionResponse,
    summary="Get player session",
    description=(
        "Return the current player session state. The backend tracks playback "
        "metadata only; demo audio is played client-side."
    ),
)
def get_player(
    player_service: Annotated[PlayerService, Depends(get_player_service)],
) -> PlayerSessionResponse:
    """Return the current player session."""
    return player_service.get_session()


@router.put(
    "/play",
    response_model=PlayerSessionResponse,
    summary="Start or resume playback",
    description=(
        "Play a specific demo track or resume the current session. "
        "When no track ID is supplied, playback resumes or starts the queue."
    ),
)
def play_track(
    player_service: Annotated[PlayerService, Depends(get_player_service)],
    request: PlayRequest | None = None,
) -> PlayerSessionResponse:
    """Start or resume playback."""
    track_id = request.track_id if request is not None else None
    return player_service.play(track_id=track_id)


@router.put(
    "/pause",
    response_model=PlayerSessionResponse,
    summary="Pause playback",
    description="Pause the currently active track.",
)
def pause_playback(
    player_service: Annotated[PlayerService, Depends(get_player_service)],
) -> PlayerSessionResponse:
    """Pause playback."""
    return player_service.pause()


@router.put(
    "/seek",
    response_model=PlayerSessionResponse,
    summary="Seek within active track",
    description="Update the playback position for the active track.",
)
def seek_playback(
    request: SeekRequest,
    player_service: Annotated[PlayerService, Depends(get_player_service)],
) -> PlayerSessionResponse:
    """Seek within the active track."""
    return player_service.seek(request.position_ms)


@router.put(
    "/volume",
    response_model=PlayerSessionResponse,
    summary="Set player volume",
    description="Update normalized session volume between 0.0 and 1.0.",
)
def set_volume(
    request: VolumeRequest,
    player_service: Annotated[PlayerService, Depends(get_player_service)],
) -> PlayerSessionResponse:
    """Update session volume."""
    return player_service.set_volume(request.level)


@router.put(
    "/shuffle",
    response_model=PlayerSessionResponse,
    summary="Set shuffle mode",
    description="Enable or disable shuffle mode for queue navigation.",
)
def set_shuffle(
    request: ShuffleRequest,
    player_service: Annotated[PlayerService, Depends(get_player_service)],
) -> PlayerSessionResponse:
    """Update shuffle mode."""
    return player_service.set_shuffle(request.enabled)


@router.put(
    "/repeat",
    response_model=PlayerSessionResponse,
    summary="Set repeat mode",
    description="Update repeat mode for queue playback.",
)
def set_repeat(
    request: RepeatRequest,
    player_service: Annotated[PlayerService, Depends(get_player_service)],
) -> PlayerSessionResponse:
    """Update repeat mode."""
    return player_service.set_repeat(request.mode)


@router.post(
    "/next",
    response_model=PlayerSessionResponse,
    summary="Next track",
    description="Advance to the next track using queue and repeat rules.",
)
def next_track(
    player_service: Annotated[PlayerService, Depends(get_player_service)],
) -> PlayerSessionResponse:
    """Advance to the next track."""
    return player_service.next_track()


@router.post(
    "/previous",
    response_model=PlayerSessionResponse,
    summary="Previous track",
    description=(
        "Restart the active track when past the restart threshold, "
        "otherwise move to the previous queue item."
    ),
)
def previous_track(
    player_service: Annotated[PlayerService, Depends(get_player_service)],
) -> PlayerSessionResponse:
    """Move to the previous track."""
    return player_service.previous_track()


@router.post(
    "/queue",
    response_model=PlayerSessionResponse,
    summary="Add track to queue",
    description="Append a demo catalog track to the player queue.",
    responses={409: {"description": "Duplicate queue entry disallowed"}},
)
def add_to_queue(
    request: QueueTrackRequest,
    player_service: Annotated[PlayerService, Depends(get_player_service)],
) -> PlayerSessionResponse:
    """Append a track to the queue."""
    return player_service.add_to_queue(
        request.track_id,
        allow_duplicate=request.allow_duplicate,
    )


@router.delete(
    "/queue/{track_id}",
    response_model=PlayerSessionResponse,
    summary="Remove track from queue",
    description="Remove a track from the player queue by catalog track ID.",
    responses={404: {"description": "Queue item not found"}},
)
def remove_from_queue(
    track_id: str,
    player_service: Annotated[PlayerService, Depends(get_player_service)],
) -> PlayerSessionResponse:
    """Remove a track from the queue."""
    return player_service.remove_from_queue(track_id)
