"""Map player session ORM records to Pydantic domain models."""

from musicbloom.db.models.player_session import PlayerSessionRecord
from musicbloom.models.player import (
    ActiveTrack,
    PlaybackState,
    PlayerSession,
    QueueItem,
    RepeatMode,
    Volume,
    create_initial_player_session,
)


def record_to_player_session(record: PlayerSessionRecord) -> PlayerSession:
    """Convert a database record into a Pydantic player session."""
    active_track = (
        ActiveTrack.model_validate(record.active_track)
        if record.active_track is not None
        else None
    )
    queue = [QueueItem.model_validate(item) for item in record.queue]
    return PlayerSession(
        state=PlaybackState(record.state),
        active_track=active_track,
        queue=queue,
        queue_index=record.queue_index,
        volume=Volume(level=record.volume_level),
        shuffle=record.shuffle,
        repeat_mode=RepeatMode(record.repeat_mode),
    )


def apply_player_session_to_record(
    record: PlayerSessionRecord,
    session: PlayerSession,
) -> None:
    """Apply Pydantic player session values onto a database record."""
    record.state = session.state.value
    record.volume_level = session.volume.level
    record.shuffle = session.shuffle
    record.repeat_mode = session.repeat_mode.value
    record.queue_index = session.queue_index
    record.active_track = (
        session.active_track.model_dump(mode="json")
        if session.active_track is not None
        else None
    )
    record.queue = [item.model_dump(mode="json") for item in session.queue]


def create_default_player_session_record(user_id: int) -> PlayerSessionRecord:
    """Build a default player session ORM entity for a user."""
    initial = create_initial_player_session()
    record = PlayerSessionRecord(
        user_id=user_id,
        state=initial.state.value,
        volume_level=initial.volume.level,
        shuffle=initial.shuffle,
        repeat_mode=initial.repeat_mode.value,
        queue_index=initial.queue_index,
        active_track=None,
        queue=[],
    )
    apply_player_session_to_record(record, initial)
    return record
