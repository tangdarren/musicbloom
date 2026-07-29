"""Unit tests for player domain models."""

import pytest
from pydantic import ValidationError

from musicbloom.models.player import (
    PlaybackPosition,
    PlaybackState,
    PlayerSession,
    Volume,
    create_initial_player_session,
)


def test_create_initial_player_session_defaults() -> None:
    session = create_initial_player_session()

    assert session.state == PlaybackState.STOPPED
    assert session.active_track is None
    assert session.queue == []
    assert session.queue_index is None
    assert session.volume.level == 0.8
    assert session.shuffle is False


def test_volume_rejects_out_of_range_values() -> None:
    with pytest.raises(ValidationError):
        Volume(level=1.5)


def test_playback_position_rejects_negative_values() -> None:
    with pytest.raises(ValidationError):
        PlaybackPosition(position_ms=-1)


def test_playback_position_clamps_to_duration() -> None:
    position = PlaybackPosition(position_ms=500).clamp_to_duration(250)
    assert position.position_ms == 250


def test_playback_position_rejects_negative_duration() -> None:
    with pytest.raises(ValueError, match="duration_ms must be non-negative"):
        PlaybackPosition(position_ms=100).clamp_to_duration(-1)


def test_player_session_rejects_invalid_queue_index() -> None:
    session = create_initial_player_session()
    payload = session.model_dump()
    payload["queue_index"] = 0
    with pytest.raises(ValidationError):
        PlayerSession.model_validate(payload)
