import pytest
from fastapi import HTTPException

from app.auth import APIKeyAuthenticator, Principal, Role


def test_authenticator_resolves_principal_with_constant_time_comparison() -> None:
    authenticator = APIKeyAuthenticator({"secret": Principal("user-1", Role.OPERATOR)})
    assert authenticator.authenticate("secret") == Principal("user-1", Role.OPERATOR)


def test_missing_or_unknown_key_is_unauthorized() -> None:
    authenticator = APIKeyAuthenticator({"secret": Principal("user-1", Role.OPERATOR)})
    with pytest.raises(HTTPException) as error:
        authenticator.authenticate("unknown")
    assert error.value.status_code == 401


def test_authenticator_requires_at_least_one_key() -> None:
    with pytest.raises(ValueError, match="at least one"):
        APIKeyAuthenticator({})


def test_environment_parser_supports_multiple_roles(monkeypatch) -> None:
    monkeypatch.setenv("API_KEYS", "read:viewer:analyst,write:operator:clerk")
    authenticator = APIKeyAuthenticator.from_environment()
    assert authenticator.authenticate("read").role is Role.VIEWER
    assert authenticator.authenticate("write").role is Role.OPERATOR


def test_environment_parser_fails_when_keys_are_missing(monkeypatch) -> None:
    monkeypatch.delenv("API_KEYS", raising=False)
    with pytest.raises(RuntimeError, match="must be configured"):
        APIKeyAuthenticator.from_environment()
