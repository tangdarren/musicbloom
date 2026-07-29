"""Quest and achievement service errors."""


class QuestAchievementServiceError(Exception):
    """Base quest and achievement service error with an HTTP status code."""

    status_code: int = 400

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class QuestNotFoundError(QuestAchievementServiceError):
    """Raised when a quest cannot be resolved."""

    status_code = 404


class AchievementNotFoundError(QuestAchievementServiceError):
    """Raised when an achievement cannot be resolved."""

    status_code = 404


class RewardNotFoundError(QuestAchievementServiceError):
    """Raised when a reward definition cannot be resolved."""

    status_code = 404


class RewardNotClaimableError(QuestAchievementServiceError):
    """Raised when a reward is not ready to be claimed."""

    status_code = 409


class RewardAlreadyClaimedError(QuestAchievementServiceError):
    """Raised when a reward has already been claimed."""

    status_code = 409
