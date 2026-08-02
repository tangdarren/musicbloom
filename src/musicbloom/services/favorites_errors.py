"""Favorites service errors."""


class FavoritesServiceError(Exception):
    """Base favorites service error with an HTTP status code."""

    status_code: int = 400

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class FavoriteTrackNotFoundError(FavoritesServiceError):
    """Raised when a catalog track cannot be resolved for favoriting."""

    status_code = 404
