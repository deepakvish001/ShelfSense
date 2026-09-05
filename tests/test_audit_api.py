from fastapi.testclient import TestClient

from app.inventory import InventoryLedger
from app.main import create_app
from app.store import SQLiteStore


def test_write_operation_is_visible_in_admin_audit_feed(
    tmp_path,
    authenticator,
    admin_headers,
) -> None:
    store = SQLiteStore(tmp_path / "audit.db")
    api = TestClient(
        create_app(InventoryLedger(), store, authenticator),
        headers=admin_headers,
    )
    response = api.post(
        "/api/v1/products",
        json={
            "sku": "SOAP",
            "name": "Soap",
            "category": "Care",
            "selling_price": "35.00",
        },
    )
    audit = api.get("/api/v1/audit-events")
    assert response.status_code == 201
    assert audit.status_code == 200
    assert audit.json()[0]["action"] == "product.created"
    assert audit.json()[0]["resource"] == "SOAP"


def test_non_admin_cannot_read_audit_feed(tmp_path, authenticator) -> None:
    store = SQLiteStore(tmp_path / "forbidden.db")
    api = TestClient(
        create_app(InventoryLedger(), store, authenticator),
        headers={"X-API-Key": "viewer-key"},
    )
    assert api.get("/api/v1/audit-events").status_code == 403
