import pytest

from app.auth import APIKeyAuthenticator, Principal, Role


@pytest.fixture
def authenticator() -> APIKeyAuthenticator:
    return APIKeyAuthenticator(
        {
            "viewer-key": Principal("test-viewer", Role.VIEWER),
            "operator-key": Principal("test-operator", Role.OPERATOR),
            "admin-key": Principal("test-admin", Role.ADMIN),
        }
    )


@pytest.fixture
def admin_headers() -> dict[str, str]:
    return {"X-API-Key": "admin-key"}
