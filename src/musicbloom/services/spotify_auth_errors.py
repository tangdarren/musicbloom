"""Spotify authentication service errors."""


class SpotifyAuthServiceError(Exception):
    """Base Spotify auth service error with an HTTP status code."""

    status_code: int = 400

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class SpotifyNotConfiguredError(SpotifyAuthServiceError):
    """Raised when Spotify OAuth is not configured."""

    status_code = 503


class OAuthStateMismatchError(SpotifyAuthServiceError):
    """Raised when OAuth state validation fails."""

    status_code = 400


class AuthorizationDeniedError(SpotifyAuthServiceError):
    """Raised when the user denies Spotify authorization."""

    status_code = 400


class SpotifyTokenError(SpotifyAuthServiceError):
    """Raised when Spotify token exchange or refresh fails."""

    status_code = 502


class SpotifyConnectionNotFoundError(SpotifyAuthServiceError):
    """Raised when no Spotify connection exists for the user."""

    status_code = 404
