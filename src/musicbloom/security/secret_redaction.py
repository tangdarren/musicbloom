"""Utilities for redacting secrets from logs, errors, and API payloads."""

from collections.abc import Iterable


def redact_secrets(text: str, secrets: Iterable[str]) -> str:
    """Replace known secret values with a fixed redaction token."""
    redacted = text
    for secret in secrets:
        if not secret:
            continue
        redacted = redacted.replace(secret, "[REDACTED]")
    return redacted


def redact_basic_auth_header(text: str) -> str:
    """Redact HTTP Basic authorization header values."""
    lowered = text.lower()
    marker = "authorization: basic "
    start = lowered.find(marker)
    if start == -1:
        return text
    value_start = start + len(marker)
    value_end = text.find("\n", value_start)
    if value_end == -1:
        value_end = len(text)
    return f"{text[:value_start]}[REDACTED]{text[value_end:]}"
