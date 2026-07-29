"""FastAPI dependency providers."""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from musicbloom.config import Settings
from musicbloom.db.init import get_demo_user
from musicbloom.db.session import get_db
from musicbloom.repositories.achievement_progress import AchievementProgressRepository
from musicbloom.repositories.database_player import DatabasePlayerSessionRepository
from musicbloom.repositories.decoration_unlock import DecorationUnlockRepository
from musicbloom.repositories.demo_catalog import DemoCatalogRepository
from musicbloom.repositories.demo_rewards_catalog import DemoRewardsCatalogRepository
from musicbloom.repositories.equipped_decoration import EquippedDecorationRepository
from musicbloom.repositories.garden_profile import GardenProfileRepository
from musicbloom.repositories.listening_event import ListeningEventRepository
from musicbloom.repositories.melody_points_transaction import (
    MelodyPointsTransactionRepository,
)
from musicbloom.repositories.player import PlayerSessionRepository
from musicbloom.repositories.quest_progress import QuestProgressRepository
from musicbloom.repositories.reward_claim import RewardClaimRepository
from musicbloom.repositories.track_listening_state import TrackListeningStateRepository
from musicbloom.repositories.user_progress import UserProgressRepository
from musicbloom.services.catalog import CatalogService
from musicbloom.services.garden import GardenService
from musicbloom.services.player import PlayerService
from musicbloom.services.progression import ProgressionService
from musicbloom.services.quest_achievement import QuestAchievementService


@lru_cache
def get_settings() -> Settings:
    """Return application settings."""
    return Settings()


def get_demo_catalog_repository() -> DemoCatalogRepository:
    """Return demo catalog repository."""
    return DemoCatalogRepository()


def get_demo_rewards_catalog_repository() -> DemoRewardsCatalogRepository:
    """Return demo rewards catalog repository."""
    return DemoRewardsCatalogRepository()


def get_player_session_repository(
    db: Annotated[Session, Depends(get_db)],
) -> PlayerSessionRepository:
    """Return database-backed player session repository for the demo user."""
    return DatabasePlayerSessionRepository.for_demo_user(db)


def get_catalog_service(
    repository: Annotated[
        DemoCatalogRepository,
        Depends(get_demo_catalog_repository),
    ],
) -> CatalogService:
    """Return catalog service backed by the demo repository."""
    return CatalogService(repository)


def get_player_service(
    player_repository: Annotated[
        PlayerSessionRepository,
        Depends(get_player_session_repository),
    ],
    catalog_repository: Annotated[
        DemoCatalogRepository,
        Depends(get_demo_catalog_repository),
    ],
) -> PlayerService:
    """Return player service backed by database session storage."""
    return PlayerService(player_repository, catalog_repository)


CatalogServiceDep = Annotated[CatalogService, Depends(get_catalog_service)]
PlayerServiceDep = Annotated[PlayerService, Depends(get_player_service)]


def get_quest_achievement_service(
    db: Annotated[Session, Depends(get_db)],
    catalog_service: Annotated[CatalogService, Depends(get_catalog_service)],
    rewards_catalog: Annotated[
        DemoRewardsCatalogRepository,
        Depends(get_demo_rewards_catalog_repository),
    ],
) -> QuestAchievementService:
    """Return quest and achievement service scoped to the demo user."""
    demo_user = get_demo_user(db)
    return QuestAchievementService(
        user_id=demo_user.id,
        catalog_service=catalog_service,
        rewards_catalog=rewards_catalog,
        quest_progress_repository=QuestProgressRepository(db),
        achievement_progress_repository=AchievementProgressRepository(db),
        reward_claim_repository=RewardClaimRepository(db),
        decoration_unlock_repository=DecorationUnlockRepository(db),
        listening_event_repository=ListeningEventRepository(db),
        track_state_repository=TrackListeningStateRepository(db),
        user_progress_repository=UserProgressRepository(db),
    )


QuestAchievementServiceDep = Annotated[
    QuestAchievementService,
    Depends(get_quest_achievement_service),
]


def get_progression_service(
    db: Annotated[Session, Depends(get_db)],
    catalog_service: Annotated[CatalogService, Depends(get_catalog_service)],
    quest_service: Annotated[
        QuestAchievementService,
        Depends(get_quest_achievement_service),
    ],
) -> ProgressionService:
    """Return progression service scoped to the demo user."""
    demo_user = get_demo_user(db)
    return ProgressionService(
        user_id=demo_user.id,
        catalog_service=catalog_service,
        listening_event_repository=ListeningEventRepository(db),
        track_state_repository=TrackListeningStateRepository(db),
        transaction_repository=MelodyPointsTransactionRepository(db),
        progress_repository=UserProgressRepository(db),
        quest_achievement_service=quest_service,
    )


ProgressionServiceDep = Annotated[ProgressionService, Depends(get_progression_service)]


def get_garden_service(
    db: Annotated[Session, Depends(get_db)],
    catalog_service: Annotated[CatalogService, Depends(get_catalog_service)],
    rewards_catalog: Annotated[
        DemoRewardsCatalogRepository,
        Depends(get_demo_rewards_catalog_repository),
    ],
) -> GardenService:
    """Return garden service scoped to the demo user."""
    demo_user = get_demo_user(db)
    return GardenService(
        user_id=demo_user.id,
        catalog_service=catalog_service,
        rewards_catalog=rewards_catalog,
        garden_profile_repository=GardenProfileRepository(db),
        equipped_decoration_repository=EquippedDecorationRepository(db),
        decoration_unlock_repository=DecorationUnlockRepository(db),
        user_progress_repository=UserProgressRepository(db),
        track_state_repository=TrackListeningStateRepository(db),
        achievement_progress_repository=AchievementProgressRepository(db),
    )


GardenServiceDep = Annotated[GardenService, Depends(get_garden_service)]
