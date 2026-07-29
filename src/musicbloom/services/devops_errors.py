"""Azure DevOps service errors."""


class DevOpsServiceError(Exception):
    """Base error for Azure DevOps service failures."""

    status_code: int = 502

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class DevOpsNotConfiguredError(DevOpsServiceError):
    """Raised when Azure DevOps credentials are missing."""

    status_code = 503


class DevOpsAuthenticationError(DevOpsServiceError):
    """Raised when Azure DevOps rejects the personal access token."""

    status_code = 401


class DevOpsAuthorizationError(DevOpsServiceError):
    """Raised when Azure DevOps denies access to the requested resource."""

    status_code = 403


class DevOpsRateLimitedError(DevOpsServiceError):
    """Raised when Azure DevOps rate limits requests."""

    status_code = 429


class DevOpsApiError(DevOpsServiceError):
    """Raised when Azure DevOps returns an unexpected failure."""

    status_code = 502
