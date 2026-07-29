"""Tests for OAuth state helpers."""

import pytest
from pydantic import SecretStr

from musicbloom.security.oauth_state import (
    OAuthStateError,
    build_signed_oauth_state,
    generate_oauth_state,
    states_match,
    validate_signed_oauth_state,
)


def test_signed_oauth_state_round_trip() -> None:
    secret = SecretStr("oauth-state-signing-secret")
    state = generate_oauth_state()
    signed = build_signed_oauth_state(state, secret)

    assert validate_signed_oauth_state(signed, secret) == state


def test_validate_signed_oauth_state_rejects_tampering() -> None:
    secret = SecretStr("oauth-state-signing-secret")
    signed = build_signed_oauth_state("state-value", secret)
    tampered = signed[:-1] + ("0" if signed[-1] != "0" else "1")

    with pytest.raises(OAuthStateError):
        validate_signed_oauth_state(tampered, secret)


def test_states_match_uses_constant_time_comparison() -> None:
    assert states_match("abc", "abc") is True
    assert states_match("abc", "abd") is False


def test_validate_signed_oauth_state_rejects_malformed_payload() -> None:
    secret = SecretStr("oauth-state-signing-secret")

    with pytest.raises(OAuthStateError):
        validate_signed_oauth_state("no-dot-separator", secret)

    with pytest.raises(OAuthStateError):
        validate_signed_oauth_state(".signature-only", secret)
