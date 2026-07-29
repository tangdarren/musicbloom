"""Progression domain service errors."""


class ProgressionServiceError(Exception):
    """Base progression service error with an HTTP status code."""

    status_code: int = 400

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class TrackNotFoundError(ProgressionServiceError):
    """Raised when a catalog track cannot be resolved."""

    status_code = 404


class InvalidListeningEventError(ProgressionServiceError):
    """Raised when a listening event payload is invalid."""

    status_code = 400


class InvalidListeningDurationError(ProgressionServiceError):
    """Raised when listening time fails validation."""

    status_code = 400
