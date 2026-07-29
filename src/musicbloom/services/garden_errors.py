"""Garden service errors."""


class GardenServiceError(Exception):
    """Base garden service error with an HTTP status code."""

    status_code: int = 400

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class DecorationNotFoundError(GardenServiceError):
    """Raised when a decoration cannot be resolved."""

    status_code = 404


class DecorationLockedError(GardenServiceError):
    """Raised when attempting to equip a locked decoration."""

    status_code = 409


class DecorationNotEquippedError(GardenServiceError):
    """Raised when attempting to unequip a decoration that is not equipped."""

    status_code = 404


class GardenProfileNotFoundError(GardenServiceError):
    """Raised when a garden profile cannot be resolved."""

    status_code = 404
