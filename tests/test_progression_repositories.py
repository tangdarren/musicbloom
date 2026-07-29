"""Tests for progression repository helpers."""

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from musicbloom.db.init import get_demo_user
from musicbloom.repositories.listening_event import ListeningEventRepository
from musicbloom.repositories.melody_points_transaction import (
    MelodyPointsTransactionRepository,
)
from musicbloom.repositories.track_listening_state import TrackListeningStateRepository


def test_track_listening_state_repository(db_session: Session) -> None:
    user = get_demo_user(db_session)
    repository = TrackListeningStateRepository(db_session)

    created = repository.get_or_create(user_id=user.id, track_id="demo-track-001")
    same = repository.get_or_create(user_id=user.id, track_id="demo-track-001")
    created.completion_awarded = True
    db_session.flush()

    assert created.id == same.id
    assert repository.count_completed_for_user(user.id) == 1


def test_melody_points_transaction_repository(db_session: Session) -> None:
    user = get_demo_user(db_session)
    events = ListeningEventRepository(db_session)
    transactions = MelodyPointsTransactionRepository(db_session)

    event = events.add_event(
        user_id=user.id,
        track_id="demo-track-001",
        event_type="progress",
        idempotency_key="transaction-event",
        position_ms=30_000,
        occurred_at=datetime.now(tz=UTC),
    )
    transaction = transactions.add_transaction(
        user_id=user.id,
        amount=4,
        experience_amount=6,
        reason="listening_progress",
        explanation="Test award",
        track_id="demo-track-001",
        listening_event_id=event.id,
    )

    assert transactions.count_for_user(user.id) == 1
    assert transactions.list_for_event(event.id)[0].id == transaction.id


def test_listening_event_idempotency_lookup(db_session: Session) -> None:
    user = get_demo_user(db_session)
    repository = ListeningEventRepository(db_session)

    repository.add_event(
        user_id=user.id,
        track_id="demo-track-001",
        event_type="started",
        idempotency_key="lookup-key",
        position_ms=0,
        occurred_at=datetime.now(tz=UTC),
    )

    found = repository.get_by_idempotency_key(
        user_id=user.id,
        idempotency_key="lookup-key",
    )

    assert found is not None
    assert found.track_id == "demo-track-001"
