"""Spotify playback service errors."""


class SpotifyPlaybackServiceError(Exception):
    """Base Spotify playback service error with an HTTP status code."""

    status_code: int = 400

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class SpotifyPlaybackNotConfiguredError(SpotifyPlaybackServiceError):
    """Raised when Spotify OAuth is not configured."""

    status_code = 503


class SpotifyPlaybackNotConnectedError(SpotifyPlaybackServiceError):
    """Raised when no Spotify account is connected."""

    status_code = 404


class SpotifyNoActiveDeviceError(SpotifyPlaybackServiceError):
    """Raised when Spotify has no active playback device."""

    status_code = 409


class SpotifyNoActivePlaybackError(SpotifyPlaybackServiceError):
    """Raised when no active playback context exists for an action."""

    status_code = 409


class SpotifyInsufficientScopeError(SpotifyPlaybackServiceError):
    """Raised when the connected account lacks required scopes."""

    status_code = 403


class SpotifyRateLimitedError(SpotifyPlaybackServiceError):
    """Raised when Spotify returns a rate-limit response."""

    status_code = 429


class SpotifyPlaybackApiError(SpotifyPlaybackServiceError):
    """Raised when Spotify returns an unexpected API error."""

    status_code = 502


class SpotifyTokenUnavailableError(SpotifyPlaybackServiceError):
    """Raised when a valid Spotify access token is unavailable."""

    status_code = 401
