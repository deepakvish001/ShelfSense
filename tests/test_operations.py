from uuid import UUID

from fastapi.testclient import TestClient

from app.config import Environment, Settings
from app.inventory import InventoryLedger
from app.main import create_app
from app.store import SQLiteStore


def test_health_and_readiness_include_security_headers(
    tmp_path,
    authenticator,
) -> None:
    store = SQLiteStore(tmp_path / "operations.db")
    api = TestClient(
        create_app(
            InventoryLedger(),
            store,
            authenticator,
            Settings(Environment.TEST, str(tmp_path / "unused.db"), ()),
        )
    )
    health = api.get("/healthz")
    readiness = api.get("/readyz")
    assert health.status_code == 200
    assert readiness.json() == {"status": "ready"}
    assert health.headers["x-content-type-options"] == "nosniff"
    assert health.headers["x-frame-options"] == "DENY"
    UUID(health.headers["x-request-id"])


def test_valid_caller_request_id_is_preserved(tmp_path, authenticator) -> None:
    request_id = "de305d54-75b4-431b-adb2-eb6b9e546014"
    api = TestClient(
        create_app(
            InventoryLedger(),
            SQLiteStore(tmp_path / "request-id.db"),
            authenticator,
        )
    )
    response = api.get("/healthz", headers={"X-Request-ID": request_id})
    assert response.headers["x-request-id"] == request_id


def test_production_enables_transport_security_header(tmp_path, authenticator) -> None:
    api = TestClient(
        create_app(
            InventoryLedger(),
            SQLiteStore(tmp_path / "production.db"),
            authenticator,
            Settings(Environment.PRODUCTION, "unused.db", ()),
        )
    )
    response = api.get("/healthz")
    assert response.headers["strict-transport-security"].startswith("max-age=")
