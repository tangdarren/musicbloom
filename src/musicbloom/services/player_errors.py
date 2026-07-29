"""Player domain service errors."""


class PlayerServiceError(Exception):
    """Base player service error with an HTTP status code."""

    status_code: int = 400

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class TrackNotFoundError(PlayerServiceError):
    """Raised when a catalog track cannot be resolved."""

    status_code = 404


class TrackNotPlayableError(PlayerServiceError):
    """Raised when a track is unavailable in demo mode."""

    status_code = 400


class QueueItemNotFoundError(PlayerServiceError):
    """Raised when a queue item cannot be found."""

    status_code = 404


class DuplicateQueueItemError(PlayerServiceError):
    """Raised when duplicate queue entries are disallowed."""

    status_code = 409


class NothingToPlayError(PlayerServiceError):
    """Raised when playback is requested with no available content."""

    status_code = 409


class InvalidPlaybackStateError(PlayerServiceError):
    """Raised when an action is invalid for the current transport state."""

    status_code = 409


class InvalidSeekPositionError(PlayerServiceError):
    """Raised when a seek position is outside the active track bounds."""

    status_code = 400
