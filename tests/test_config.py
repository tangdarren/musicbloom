"""Tests for application configuration."""

import pytest
from pydantic import SecretStr, ValidationError

from musicbloom.config import DEFAULT_CORS_ORIGINS, Settings, _parse_cors_origins
from musicbloom.dependencies import get_settings


def test_default_settings() -> None:
    settings = Settings()

    assert settings.environment == "development"
    assert settings.debug is True
    assert settings.api_host == "0.0.0.0"
    assert settings.api_port == 8000
    assert settings.database_url is None
    assert settings.demo_mode is True
    assert settings.cors_origins == DEFAULT_CORS_ORIGINS
    assert settings.secret_key is None


def test_environment_variable_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MUSICBLOOM_ENVIRONMENT", "staging")
    monkeypatch.setenv("MUSICBLOOM_DEBUG", "false")
    monkeypatch.setenv("MUSICBLOOM_API_HOST", "127.0.0.1")
    monkeypatch.setenv("MUSICBLOOM_API_PORT", "9000")
    monkeypatch.setenv(
        "MUSICBLOOM_DATABASE_URL",
        "postgresql://localhost:5432/musicbloom",
    )
    monkeypatch.setenv(
        "MUSICBLOOM_CORS_ORIGINS",
        "https://app.example.com,https://admin.example.com",
    )

    settings = Settings()

    assert settings.environment == "staging"
    assert settings.debug is False
    assert settings.api_host == "127.0.0.1"
    assert settings.api_port == 9000
    assert settings.database_url == "postgresql://localhost:5432/musicbloom"
    assert settings.cors_origins == [
        "https://app.example.com",
        "https://admin.example.com",
    ]


def test_demo_mode_defaults_to_enabled() -> None:
    settings = Settings()
    assert settings.demo_mode is True


def test_demo_mode_can_be_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MUSICBLOOM_DEMO_MODE", "false")
    settings = Settings()
    assert settings.demo_mode is False


def test_secret_key_is_masked_in_repr_and_str() -> None:
    settings = Settings(secret_key=SecretStr("super-secret-development-key"))

    rendered = repr(settings)
    assert "super-secret-development-key" not in rendered
    assert "**********" in rendered

    assert "super-secret-development-key" not in str(settings)


def test_secret_key_is_masked_in_model_dump() -> None:
    settings = Settings(secret_key=SecretStr("super-secret-development-key"))
    dumped = settings.model_dump()

    assert dumped["secret_key"] is not None
    assert "super-secret-development-key" not in str(dumped["secret_key"])


@pytest.mark.parametrize(
    ("kwargs", "expected_message"),
    [
        (
            {
                "environment": "production",
                "secret_key": None,
                "demo_mode": False,
                "debug": False,
                "database_url": "postgresql://localhost/musicbloom",
            },
            "secret_key is required in production",
        ),
        (
            {
                "environment": "production",
                "secret_key": SecretStr("short"),
                "demo_mode": False,
                "debug": False,
                "database_url": "postgresql://localhost/musicbloom",
            },
            "secret_key must be at least 32 characters in production",
        ),
        (
            {
                "environment": "production",
                "secret_key": SecretStr("x" * 32),
                "demo_mode": True,
                "debug": False,
                "database_url": "postgresql://localhost/musicbloom",
            },
            "demo_mode must be disabled in production",
        ),
        (
            {
                "environment": "production",
                "secret_key": SecretStr("x" * 32),
                "demo_mode": False,
                "debug": True,
                "database_url": "postgresql://localhost/musicbloom",
            },
            "debug must be disabled in production",
        ),
        (
            {
                "environment": "production",
                "secret_key": SecretStr("x" * 32),
                "demo_mode": False,
                "debug": False,
                "database_url": None,
            },
            "database_url is required in production",
        ),
    ],
)
def test_invalid_production_configuration(
    kwargs: dict[str, object],
    expected_message: str,
) -> None:
    with pytest.raises(ValidationError) as exc_info:
        Settings(**kwargs)

    assert expected_message in str(exc_info.value)


def test_resolved_database_url_defaults_to_sqlite() -> None:
    settings = Settings()
    assert settings.resolved_database_url == "sqlite:///./musicbloom.db"


def test_resolved_database_url_uses_explicit_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "MUSICBLOOM_DATABASE_URL",
        "postgresql+psycopg://localhost/musicbloom",
    )
    settings = Settings()
    assert settings.resolved_database_url == "postgresql+psycopg://localhost/musicbloom"


def test_valid_production_configuration() -> None:
    settings = Settings(
        environment="production",
        secret_key=SecretStr("production-secret-key-with-32-chars!!"),
        demo_mode=False,
        debug=False,
        database_url="postgresql://localhost:5432/musicbloom",
    )

    assert settings.environment == "production"
    assert settings.demo_mode is False
    assert settings.debug is False


def test_cors_origins_list_input() -> None:
    settings = Settings(cors_origins=["https://example.com"])
    assert settings.cors_origins == ["https://example.com"]


def test_cors_origins_none_uses_defaults() -> None:
    settings = Settings.model_validate({"cors_origins": None})
    assert settings.cors_origins == DEFAULT_CORS_ORIGINS


def test_parse_cors_origins_accepts_list() -> None:
    origins = ["https://a.example.com", "https://b.example.com"]
    assert _parse_cors_origins(origins) == origins


def test_invalid_cors_origins_type_raises_type_error() -> None:
    with pytest.raises(
        TypeError,
        match="cors_origins must be a comma-separated string",
    ):
        Settings.model_validate({"cors_origins": 123})


def test_get_settings_is_cached() -> None:
    first = get_settings()
    second = get_settings()
    assert first is second


def test_secret_key_unset_in_repr() -> None:
    settings = Settings()
    assert "secret_key=unset" in repr(settings)
