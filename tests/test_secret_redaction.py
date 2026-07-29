"""Tests for secret redaction utilities."""

from musicbloom.security.secret_redaction import (
    redact_basic_auth_header,
    redact_secrets,
)


def test_redact_secrets_replaces_known_values() -> None:
    text = "token=super-secret-token and again super-secret-token"
    assert redact_secrets(text, ["super-secret-token"]) == (
        "token=[REDACTED] and again [REDACTED]"
    )


def test_redact_secrets_ignores_empty_values() -> None:
    assert redact_secrets("unchanged", ["", None]) == "unchanged"  # type: ignore[list-item]


def test_redact_basic_auth_header() -> None:
    text = "Authorization: Basic abc123\nContent-Type: application/json"
    assert redact_basic_auth_header(text) == (
        "Authorization: Basic [REDACTED]\nContent-Type: application/json"
    )


def test_redact_basic_auth_header_without_marker() -> None:
    assert redact_basic_auth_header("No auth here") == "No auth here"


def test_redact_basic_auth_header_without_trailing_newline() -> None:
    text = "Authorization: Basic abc123"
    assert redact_basic_auth_header(text) == "Authorization: Basic [REDACTED]"
