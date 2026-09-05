import pytest

from app.config import Environment, Settings


def test_settings_parse_origins_and_database_path(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("DATABASE_PATH", "test.db")
    monkeypatch.setenv("ALLOWED_ORIGINS", "https://one.example, https://two.example")
    settings = Settings.from_environment()
    assert settings.environment is Environment.TEST
    assert settings.database_path == "test.db"
    assert settings.allowed_origins == ("https://one.example", "https://two.example")


def test_production_rejects_wildcard_cors(monkeypatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("ALLOWED_ORIGINS", "*")
    with pytest.raises(RuntimeError, match="wildcard"):
        Settings.from_environment()
