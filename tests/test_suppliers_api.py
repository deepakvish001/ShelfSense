import pytest
from fastapi.testclient import TestClient

from app.inventory import InventoryLedger
from app.main import create_app
from app.store import SQLiteStore


@pytest.fixture
def api(tmp_path, authenticator, admin_headers) -> TestClient:
    store = SQLiteStore(tmp_path / "suppliers.db")
    return TestClient(
        create_app(InventoryLedger(), store, authenticator),
        headers=admin_headers,
    )


def test_operator_cannot_create_supplier(tmp_path, authenticator) -> None:
    store = SQLiteStore(tmp_path / "operator.db")
    api = TestClient(
        create_app(InventoryLedger(), store, authenticator),
        headers={"X-API-Key": "operator-key"},
    )
    response = api.post(
        "/api/v1/suppliers",
        json={"code": "LOCAL", "name": "Local", "phone": "+91 99999 99999"},
    )
    assert response.status_code == 403


def test_create_and_read_supplier(api: TestClient) -> None:
    created = api.post(
        "/api/v1/suppliers",
        json={
            "code": "fresh foods",
            "name": "Fresh Foods Ltd",
            "email": "orders@example.com",
        },
    )
    fetched = api.get("/api/v1/suppliers/FRESH-FOODS")
    assert created.status_code == 201
    assert fetched.status_code == 200
    assert fetched.json()["code"] == "FRESH-FOODS"


def test_duplicate_supplier_returns_conflict(api: TestClient) -> None:
    command = {
        "code": "LOCAL",
        "name": "Local Supplier",
        "phone": "+91 99999 99999",
    }
    assert api.post("/api/v1/suppliers", json=command).status_code == 201
    assert api.post("/api/v1/suppliers", json=command).status_code == 409


def test_supplier_without_contact_returns_validation_error(api: TestClient) -> None:
    response = api.post(
        "/api/v1/suppliers",
        json={"code": "LOCAL", "name": "Local Supplier"},
    )
    assert response.status_code == 422


def test_unknown_supplier_returns_not_found(api: TestClient) -> None:
    assert api.get("/api/v1/suppliers/UNKNOWN").status_code == 404
