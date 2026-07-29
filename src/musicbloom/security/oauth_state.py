"""OAuth state generation and validation."""

import hmac
import secrets
from hashlib import sha256

from pydantic import SecretStr

OAUTH_STATE_BYTES = 32


class OAuthStateError(Exception):
    """Raised when OAuth state validation fails."""


def generate_oauth_state() -> str:
    """Return a cryptographically secure OAuth state value."""
    return secrets.token_urlsafe(OAUTH_STATE_BYTES)


def sign_oauth_state(state: str, secret: SecretStr) -> str:
    """Return an HMAC signature for an OAuth state value."""
    digest = hmac.new(
        secret.get_secret_value().encode("utf-8"),
        state.encode("utf-8"),
        sha256,
    ).hexdigest()
    return digest


def build_signed_oauth_state(state: str, secret: SecretStr) -> str:
    """Return a signed OAuth state payload suitable for cookie storage."""
    return f"{state}.{sign_oauth_state(state, secret)}"


def validate_signed_oauth_state(payload: str, secret: SecretStr) -> str:
    """Validate a signed OAuth state payload and return the state value."""
    try:
        state, signature = payload.rsplit(".", 1)
    except ValueError as exc:
        raise OAuthStateError("OAuth state payload is malformed") from exc

    if not state:
        raise OAuthStateError("OAuth state payload is malformed")

    expected = sign_oauth_state(state, secret)
    if not hmac.compare_digest(signature, expected):
        raise OAuthStateError("OAuth state signature mismatch")

    return state


def states_match(expected_state: str, received_state: str) -> bool:
    """Compare OAuth state values using a constant-time comparison."""
    return hmac.compare_digest(expected_state, received_state)
