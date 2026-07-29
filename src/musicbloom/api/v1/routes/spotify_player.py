"""Spotify player routes."""

from fastapi import APIRouter

from musicbloom.api.v1.schemas.spotify_player import SpotifyPlayerResponse
from musicbloom.api.v1.schemas.spotify_player_requests import (
    SpotifySeekRequest,
    SpotifyVolumeRequest,
)
from musicbloom.dependencies import SpotifyPlaybackServiceDep

router = APIRouter(prefix="/spotify/player", tags=["spotify-player"])


@router.get(
    "",
    response_model=SpotifyPlayerResponse,
    summary="Get Spotify playback state",
    description=(
        "Return normalized Spotify playback metadata and device information. "
        "MusicBloom never downloads, proxies, or caches Spotify audio."
    ),
)
async def get_spotify_player(
    spotify_playback_service: SpotifyPlaybackServiceDep,
) -> SpotifyPlayerResponse:
    """Return current Spotify playback metadata."""
    return await spotify_playback_service.get_player()


@router.put(
    "/play",
    response_model=SpotifyPlayerResponse,
    summary="Start or resume Spotify playback",
)
async def play_spotify(
    spotify_playback_service: SpotifyPlaybackServiceDep,
) -> SpotifyPlayerResponse:
    """Resume or start Spotify playback on the active device."""
    return await spotify_playback_service.play()


@router.put(
    "/pause",
    response_model=SpotifyPlayerResponse,
    summary="Pause Spotify playback",
)
async def pause_spotify(
    spotify_playback_service: SpotifyPlaybackServiceDep,
) -> SpotifyPlayerResponse:
    """Pause Spotify playback on the active device."""
    return await spotify_playback_service.pause()


@router.post(
    "/next",
    response_model=SpotifyPlayerResponse,
    summary="Skip to next Spotify track",
)
async def next_spotify(
    spotify_playback_service: SpotifyPlaybackServiceDep,
) -> SpotifyPlayerResponse:
    """Skip to the next Spotify track."""
    return await spotify_playback_service.next_track()


@router.post(
    "/previous",
    response_model=SpotifyPlayerResponse,
    summary="Skip to previous Spotify track",
)
async def previous_spotify(
    spotify_playback_service: SpotifyPlaybackServiceDep,
) -> SpotifyPlayerResponse:
    """Skip to the previous Spotify track."""
    return await spotify_playback_service.previous_track()


@router.put(
    "/seek",
    response_model=SpotifyPlayerResponse,
    summary="Seek within active Spotify track",
)
async def seek_spotify(
    request: SpotifySeekRequest,
    spotify_playback_service: SpotifyPlaybackServiceDep,
) -> SpotifyPlayerResponse:
    """Seek within the active Spotify track."""
    return await spotify_playback_service.seek(request.position_ms)


@router.put(
    "/volume",
    response_model=SpotifyPlayerResponse,
    summary="Set Spotify playback volume",
)
async def set_spotify_volume(
    request: SpotifyVolumeRequest,
    spotify_playback_service: SpotifyPlaybackServiceDep,
) -> SpotifyPlayerResponse:
    """Set Spotify playback volume using a normalized level."""
    return await spotify_playback_service.set_volume(request.level)
