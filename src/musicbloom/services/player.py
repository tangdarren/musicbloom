"""Player session business logic."""

from musicbloom.models.catalog import Track
from musicbloom.models.player import (
    ActiveTrack,
    PlaybackPosition,
    PlaybackState,
    PlayerSession,
    QueueItem,
    RepeatMode,
    Volume,
)
from musicbloom.repositories.demo_catalog import DemoCatalogRepository
from musicbloom.repositories.player import PlayerSessionRepository
from musicbloom.services.player_errors import (
    DuplicateQueueItemError,
    InvalidPlaybackStateError,
    InvalidSeekPositionError,
    NothingToPlayError,
    QueueItemNotFoundError,
    TrackNotFoundError,
    TrackNotPlayableError,
)

PREVIOUS_RESTART_THRESHOLD_MS = 3_000


class PlayerService:
    """Business logic for player session control."""

    def __init__(
        self,
        player_repository: PlayerSessionRepository,
        catalog_repository: DemoCatalogRepository,
    ) -> None:
        self._player_repository = player_repository
        self._catalog_repository = catalog_repository

    def get_session(self) -> PlayerSession:
        """Return the current player session."""
        return self._player_repository.get_session()

    def play(self, track_id: str | None = None) -> PlayerSession:
        """Start or resume playback."""
        session = self._player_repository.get_session()

        if track_id is not None:
            track = self._require_playable_track(track_id)
            queue_index = self._find_queue_index(session, track.id)
            session = self._set_active_track(
                session,
                track,
                queue_index=queue_index,
                state=PlaybackState.PLAYING,
                position_ms=0,
            )
            return self._player_repository.save_session(session)

        if session.active_track is not None:
            if session.state == PlaybackState.PAUSED:
                session.state = PlaybackState.PLAYING
                return self._player_repository.save_session(session)
            if session.state == PlaybackState.PLAYING:
                return session
            session.state = PlaybackState.PLAYING
            return self._player_repository.save_session(session)

        if session.queue:
            index = session.queue_index if session.queue_index is not None else 0
            track = self._require_playable_track(session.queue[index].track_id)
            session = self._set_active_track(
                session,
                track,
                queue_index=index,
                state=PlaybackState.PLAYING,
                position_ms=0,
            )
            return self._player_repository.save_session(session)

        raise NothingToPlayError("Nothing is loaded or queued for playback")

    def pause(self) -> PlayerSession:
        """Pause the active track."""
        session = self._player_repository.get_session()

        if session.active_track is None:
            raise InvalidPlaybackStateError("No active track to pause")

        if session.state != PlaybackState.PLAYING:
            return session

        session.state = PlaybackState.PAUSED
        return self._player_repository.save_session(session)

    def seek(self, position_ms: int) -> PlayerSession:
        """Seek within the active track."""
        session = self._player_repository.get_session()

        if session.active_track is None:
            raise InvalidPlaybackStateError("No active track to seek")

        position = PlaybackPosition(position_ms=position_ms)
        if position.position_ms > session.active_track.duration_ms:
            raise InvalidSeekPositionError(
                "Seek position exceeds active track duration",
            )

        session.active_track.position = position
        if session.state == PlaybackState.STOPPED:
            session.state = PlaybackState.PAUSED
        return self._player_repository.save_session(session)

    def set_volume(self, level: float) -> PlayerSession:
        """Update session volume."""
        session = self._player_repository.get_session()
        session.volume = Volume(level=level)
        return self._player_repository.save_session(session)

    def set_shuffle(self, enabled: bool) -> PlayerSession:
        """Enable or disable shuffle mode."""
        session = self._player_repository.get_session()
        session.shuffle = enabled
        return self._player_repository.save_session(session)

    def set_repeat(self, mode: RepeatMode) -> PlayerSession:
        """Update repeat mode."""
        session = self._player_repository.get_session()
        session.repeat_mode = mode
        return self._player_repository.save_session(session)

    def next_track(self) -> PlayerSession:
        """Advance to the next track."""
        session = self._player_repository.get_session()

        if session.active_track is None and not session.queue:
            raise NothingToPlayError("No active track or queue items to advance")

        if session.active_track is None and session.queue:
            track = self._require_playable_track(session.queue[0].track_id)
            session = self._set_active_track(
                session,
                track,
                queue_index=0,
                state=PlaybackState.PLAYING,
                position_ms=0,
            )
            return self._player_repository.save_session(session)

        assert session.active_track is not None
        active_track = session.active_track

        if session.repeat_mode == RepeatMode.ONE:
            session = self._set_active_track(
                session,
                self._require_playable_track(active_track.track_id),
                queue_index=session.queue_index,
                state=PlaybackState.PLAYING,
                position_ms=0,
            )
            return self._player_repository.save_session(session)

        if session.queue and session.queue_index is not None:
            next_index = self._next_queue_index(session)
            if next_index is None:
                session.state = PlaybackState.STOPPED
                active_track.position = PlaybackPosition(
                    position_ms=active_track.duration_ms,
                )
                return self._player_repository.save_session(session)

            track = self._require_playable_track(session.queue[next_index].track_id)
            session = self._set_active_track(
                session,
                track,
                queue_index=next_index,
                state=PlaybackState.PLAYING,
                position_ms=0,
            )
            return self._player_repository.save_session(session)

        if session.queue:
            track = self._require_playable_track(session.queue[0].track_id)
            session = self._set_active_track(
                session,
                track,
                queue_index=0,
                state=PlaybackState.PLAYING,
                position_ms=0,
            )
            return self._player_repository.save_session(session)

        session.state = PlaybackState.STOPPED
        active_track.position = PlaybackPosition(
            position_ms=active_track.duration_ms,
        )
        return self._player_repository.save_session(session)

    def previous_track(self) -> PlayerSession:
        """Move to the previous track or restart the current track."""
        session = self._player_repository.get_session()

        if session.active_track is None and not session.queue:
            raise NothingToPlayError("No active track or queue items to rewind")

        if session.active_track is None and session.queue:
            last_index = len(session.queue) - 1
            track = self._require_playable_track(session.queue[last_index].track_id)
            session = self._set_active_track(
                session,
                track,
                queue_index=last_index,
                state=PlaybackState.PLAYING,
                position_ms=0,
            )
            return self._player_repository.save_session(session)

        assert session.active_track is not None
        active_track = session.active_track

        if active_track.position.position_ms > PREVIOUS_RESTART_THRESHOLD_MS:
            active_track.position = PlaybackPosition(position_ms=0)
            session.state = PlaybackState.PLAYING
            return self._player_repository.save_session(session)

        if session.queue and session.queue_index is not None:
            previous_index = self._previous_queue_index(session)
            track = self._require_playable_track(session.queue[previous_index].track_id)
            session = self._set_active_track(
                session,
                track,
                queue_index=previous_index,
                state=PlaybackState.PLAYING,
                position_ms=0,
            )
            return self._player_repository.save_session(session)

        active_track.position = PlaybackPosition(position_ms=0)
        session.state = PlaybackState.PLAYING
        return self._player_repository.save_session(session)

    def add_to_queue(
        self,
        track_id: str,
        *,
        allow_duplicate: bool = False,
    ) -> PlayerSession:
        """Append a catalog track to the queue."""
        track = self._get_track_or_raise(track_id)
        session = self._player_repository.get_session()

        has_duplicate = any(item.track_id == track.id for item in session.queue)
        if not allow_duplicate and has_duplicate:
            raise DuplicateQueueItemError(
                f"Track '{track.id}' is already in the queue",
            )

        session.queue.append(self._build_queue_item(track))
        return self._player_repository.save_session(session)

    def remove_from_queue(self, track_id: str) -> PlayerSession:
        """Remove a track from the queue."""
        session = self._player_repository.get_session()
        index = self._find_queue_index(session, track_id)

        if index is None:
            raise QueueItemNotFoundError(f"Track '{track_id}' is not in the queue")

        session.queue.pop(index)

        if session.queue_index is None:
            return self._player_repository.save_session(session)

        if index < session.queue_index:
            session.queue_index -= 1
        elif index == session.queue_index:
            session.queue_index = None
            session.active_track = None
            session.state = PlaybackState.STOPPED

        return self._player_repository.save_session(session)

    def _next_queue_index(self, session: PlayerSession) -> int | None:
        assert session.queue_index is not None
        if session.queue_index < len(session.queue) - 1:
            return session.queue_index + 1
        if session.repeat_mode == RepeatMode.ALL:
            return 0
        return None

    def _previous_queue_index(self, session: PlayerSession) -> int:
        assert session.queue_index is not None
        if session.queue_index > 0:
            return session.queue_index - 1
        if session.repeat_mode == RepeatMode.ALL and session.queue:
            return len(session.queue) - 1
        return 0

    def _find_queue_index(self, session: PlayerSession, track_id: str) -> int | None:
        for index, item in enumerate(session.queue):
            if item.track_id == track_id:
                return index
        return None

    def _get_track_or_raise(self, track_id: str) -> Track:
        track = self._catalog_repository.get_track(track_id)
        if track is None:
            raise TrackNotFoundError(f"Track '{track_id}' was not found")
        return track

    def _require_playable_track(self, track_id: str) -> Track:
        track = self._get_track_or_raise(track_id)
        if not track.playable_in_demo_mode:
            raise TrackNotPlayableError(
                f"Track '{track.id}' is not playable in demo mode",
            )
        return track

    def _build_queue_item(self, track: Track) -> QueueItem:
        return QueueItem(
            track_id=track.id,
            title=track.title,
            artist_name=track.artist_name,
            duration_ms=track.duration_ms,
        )

    def _build_active_track(self, track: Track, position_ms: int) -> ActiveTrack:
        return ActiveTrack(
            track_id=track.id,
            title=track.title,
            artist_name=track.artist_name,
            album_title=track.album_title,
            duration_ms=track.duration_ms,
            artwork=track.artwork,
            audio=track.audio,
            mood=track.mood,
            genre=track.genre,
            accent_theme=track.accent_theme,
            playable_in_demo_mode=track.playable_in_demo_mode,
            position=PlaybackPosition(position_ms=position_ms),
        )

    def _set_active_track(
        self,
        session: PlayerSession,
        track: Track,
        *,
        queue_index: int | None,
        state: PlaybackState,
        position_ms: int,
    ) -> PlayerSession:
        session.active_track = self._build_active_track(track, position_ms)
        session.queue_index = queue_index
        session.state = state
        return session
