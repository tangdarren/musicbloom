"""Unit tests for the player service."""

import pytest

from musicbloom.models.player import PlaybackState, RepeatMode
from musicbloom.repositories.demo_catalog import DemoCatalogRepository
from musicbloom.repositories.in_memory_player import InMemoryPlayerSessionRepository
from musicbloom.services.player import PlayerService
from musicbloom.services.player_errors import (
    DuplicateQueueItemError,
    InvalidPlaybackStateError,
    InvalidSeekPositionError,
    NothingToPlayError,
    QueueItemNotFoundError,
    TrackNotFoundError,
    TrackNotPlayableError,
)


@pytest.fixture
def player_service() -> PlayerService:
    return PlayerService(
        InMemoryPlayerSessionRepository(),
        DemoCatalogRepository(),
    )


def test_get_session_returns_stopped_defaults(player_service: PlayerService) -> None:
    session = player_service.get_session()

    assert session.state == PlaybackState.STOPPED
    assert session.active_track is None
    assert session.queue == []


def test_play_track_starts_playback(player_service: PlayerService) -> None:
    session = player_service.play(track_id="demo-track-001")

    assert session.state == PlaybackState.PLAYING
    assert session.active_track is not None
    assert session.active_track.track_id == "demo-track-001"
    assert session.active_track.position.position_ms == 0


def test_play_resumes_paused_track(player_service: PlayerService) -> None:
    player_service.play(track_id="demo-track-001")
    player_service.pause()
    session = player_service.play()

    assert session.state == PlaybackState.PLAYING


def test_play_from_queue_when_stopped(player_service: PlayerService) -> None:
    player_service.add_to_queue("demo-track-001")
    player_service.add_to_queue("demo-track-002")
    session = player_service.play()

    assert session.state == PlaybackState.PLAYING
    assert session.active_track is not None
    assert session.active_track.track_id == "demo-track-001"
    assert session.queue_index == 0


def test_play_without_content_raises(player_service: PlayerService) -> None:
    with pytest.raises(NothingToPlayError):
        player_service.play()


def test_play_unknown_track_raises(player_service: PlayerService) -> None:
    with pytest.raises(TrackNotFoundError):
        player_service.play(track_id="missing-track")


def test_play_non_playable_track_raises(player_service: PlayerService) -> None:
    with pytest.raises(TrackNotPlayableError):
        player_service.play(track_id="demo-track-008")


def test_pause_active_track(player_service: PlayerService) -> None:
    player_service.play(track_id="demo-track-001")
    session = player_service.pause()

    assert session.state == PlaybackState.PAUSED


def test_pause_without_active_track_raises(player_service: PlayerService) -> None:
    with pytest.raises(InvalidPlaybackStateError):
        player_service.pause()


def test_seek_within_active_track(player_service: PlayerService) -> None:
    player_service.play(track_id="demo-track-001")
    session = player_service.seek(60_000)

    assert session.active_track is not None
    assert session.active_track.position.position_ms == 60_000


def test_seek_beyond_duration_raises(player_service: PlayerService) -> None:
    player_service.play(track_id="demo-track-001")
    with pytest.raises(InvalidSeekPositionError):
        player_service.seek(999_999)


def test_set_volume(player_service: PlayerService) -> None:
    session = player_service.set_volume(0.25)
    assert session.volume.level == 0.25


def test_set_shuffle_and_repeat(player_service: PlayerService) -> None:
    session = player_service.set_shuffle(True)
    assert session.shuffle is True

    session = player_service.set_repeat(RepeatMode.ALL)
    assert session.repeat_mode == RepeatMode.ALL


def test_add_to_queue(player_service: PlayerService) -> None:
    session = player_service.add_to_queue("demo-track-001")

    assert len(session.queue) == 1
    assert session.queue[0].track_id == "demo-track-001"


def test_add_duplicate_queue_item_raises(player_service: PlayerService) -> None:
    player_service.add_to_queue("demo-track-001")
    with pytest.raises(DuplicateQueueItemError):
        player_service.add_to_queue("demo-track-001")


def test_add_duplicate_when_allowed(player_service: PlayerService) -> None:
    player_service.add_to_queue("demo-track-001")
    session = player_service.add_to_queue("demo-track-001", allow_duplicate=True)

    assert len(session.queue) == 2


def test_remove_from_queue(player_service: PlayerService) -> None:
    player_service.add_to_queue("demo-track-001")
    player_service.add_to_queue("demo-track-002")
    session = player_service.remove_from_queue("demo-track-001")

    assert len(session.queue) == 1
    assert session.queue[0].track_id == "demo-track-002"


def test_remove_missing_queue_item_raises(player_service: PlayerService) -> None:
    with pytest.raises(QueueItemNotFoundError):
        player_service.remove_from_queue("demo-track-001")


def test_next_advances_queue(player_service: PlayerService) -> None:
    player_service.add_to_queue("demo-track-001")
    player_service.add_to_queue("demo-track-002")
    player_service.play()
    session = player_service.next_track()

    assert session.active_track is not None
    assert session.active_track.track_id == "demo-track-002"
    assert session.queue_index == 1


def test_next_with_repeat_all_wraps(player_service: PlayerService) -> None:
    player_service.add_to_queue("demo-track-001")
    player_service.add_to_queue("demo-track-002")
    player_service.set_repeat(RepeatMode.ALL)
    player_service.play()
    player_service.next_track()
    session = player_service.next_track()

    assert session.active_track is not None
    assert session.active_track.track_id == "demo-track-001"
    assert session.queue_index == 0


def test_next_with_repeat_one_restarts(player_service: PlayerService) -> None:
    player_service.play(track_id="demo-track-001")
    player_service.seek(45_000)
    player_service.set_repeat(RepeatMode.ONE)
    session = player_service.next_track()

    assert session.active_track is not None
    assert session.active_track.track_id == "demo-track-001"
    assert session.active_track.position.position_ms == 0


def test_next_stops_at_queue_end(player_service: PlayerService) -> None:
    player_service.add_to_queue("demo-track-001")
    player_service.play()
    session = player_service.next_track()

    assert session.state == PlaybackState.STOPPED
    assert session.active_track is not None
    assert session.active_track.position.position_ms == session.active_track.duration_ms


def test_next_on_empty_queue_raises(player_service: PlayerService) -> None:
    with pytest.raises(NothingToPlayError):
        player_service.next_track()


def test_previous_restarts_when_past_threshold(player_service: PlayerService) -> None:
    player_service.play(track_id="demo-track-001")
    player_service.seek(10_000)
    session = player_service.previous_track()

    assert session.active_track is not None
    assert session.active_track.position.position_ms == 0


def test_previous_moves_to_prior_queue_item(player_service: PlayerService) -> None:
    player_service.add_to_queue("demo-track-001")
    player_service.add_to_queue("demo-track-002")
    player_service.play()
    player_service.next_track()
    session = player_service.previous_track()

    assert session.active_track is not None
    assert session.active_track.track_id == "demo-track-001"


def test_remove_active_queue_item_stops_playback(player_service: PlayerService) -> None:
    player_service.add_to_queue("demo-track-001")
    player_service.play()
    session = player_service.remove_from_queue("demo-track-001")

    assert session.state == PlaybackState.STOPPED
    assert session.active_track is None
    assert session.queue == []


def test_play_while_already_playing_is_idempotent(
    player_service: PlayerService,
) -> None:
    player_service.play(track_id="demo-track-001")
    session = player_service.play()

    assert session.state == PlaybackState.PLAYING
    assert session.active_track is not None
    assert session.active_track.track_id == "demo-track-001"


def test_play_resumes_stopped_active_track(player_service: PlayerService) -> None:
    player_service.play(track_id="demo-track-001")
    player_service.next_track()
    session = player_service.play()

    assert session.state == PlaybackState.PLAYING
    assert session.active_track is not None


def test_pause_when_already_paused_is_idempotent(player_service: PlayerService) -> None:
    player_service.play(track_id="demo-track-001")
    player_service.pause()
    session = player_service.pause()

    assert session.state == PlaybackState.PAUSED


def test_seek_while_stopped_sets_paused_state(player_service: PlayerService) -> None:
    player_service.play(track_id="demo-track-001")
    player_service.next_track()
    session = player_service.seek(10_000)

    assert session.state == PlaybackState.PAUSED
    assert session.active_track is not None
    assert session.active_track.position.position_ms == 10_000


def test_next_starts_queue_when_no_active_track(player_service: PlayerService) -> None:
    player_service.add_to_queue("demo-track-003")
    session = player_service.next_track()

    assert session.state == PlaybackState.PLAYING
    assert session.active_track is not None
    assert session.active_track.track_id == "demo-track-003"


def test_next_moves_from_direct_play_to_queue(player_service: PlayerService) -> None:
    player_service.add_to_queue("demo-track-001")
    player_service.add_to_queue("demo-track-002")
    player_service.play(track_id="demo-track-004")
    session = player_service.next_track()

    assert session.active_track is not None
    assert session.active_track.track_id == "demo-track-001"
    assert session.queue_index == 0


def test_next_stops_direct_play_without_queue(player_service: PlayerService) -> None:
    player_service.play(track_id="demo-track-001")
    session = player_service.next_track()

    assert session.state == PlaybackState.STOPPED
    assert session.active_track is not None
    assert session.active_track.position.position_ms == session.active_track.duration_ms


def test_previous_starts_last_queue_item_without_active_track(
    player_service: PlayerService,
) -> None:
    player_service.add_to_queue("demo-track-001")
    player_service.add_to_queue("demo-track-002")
    session = player_service.previous_track()

    assert session.active_track is not None
    assert session.active_track.track_id == "demo-track-002"
    assert session.queue_index == 1


def test_previous_on_direct_play_restarts_from_beginning(
    player_service: PlayerService,
) -> None:
    player_service.play(track_id="demo-track-001")
    session = player_service.previous_track()

    assert session.active_track is not None
    assert session.active_track.position.position_ms == 0


def test_previous_with_repeat_all_wraps_to_last_track(
    player_service: PlayerService,
) -> None:
    player_service.add_to_queue("demo-track-001")
    player_service.add_to_queue("demo-track-002")
    player_service.set_repeat(RepeatMode.ALL)
    player_service.play()
    session = player_service.previous_track()

    assert session.active_track is not None
    assert session.active_track.track_id == "demo-track-002"
    assert session.queue_index == 1


def test_remove_earlier_queue_item_adjusts_index(player_service: PlayerService) -> None:
    player_service.add_to_queue("demo-track-001")
    player_service.add_to_queue("demo-track-002")
    player_service.play()
    player_service.next_track()
    session = player_service.remove_from_queue("demo-track-001")

    assert session.queue_index == 0
    assert session.active_track is not None
    assert session.active_track.track_id == "demo-track-002"


def test_seek_without_active_track_raises(player_service: PlayerService) -> None:
    with pytest.raises(InvalidPlaybackStateError):
        player_service.seek(1_000)


def test_remove_later_queue_item_keeps_active_index(
    player_service: PlayerService,
) -> None:
    player_service.add_to_queue("demo-track-001")
    player_service.add_to_queue("demo-track-002")
    player_service.play()
    session = player_service.remove_from_queue("demo-track-002")

    assert session.queue_index == 0
    assert session.active_track is not None
    assert session.active_track.track_id == "demo-track-001"


def test_previous_at_first_queue_item_without_repeat_all(
    player_service: PlayerService,
) -> None:
    player_service.add_to_queue("demo-track-001")
    player_service.play()
    session = player_service.previous_track()

    assert session.queue_index == 0
    assert session.active_track is not None
    assert session.active_track.track_id == "demo-track-001"


def test_previous_on_empty_session_raises(player_service: PlayerService) -> None:
    with pytest.raises(NothingToPlayError):
        player_service.previous_track()
