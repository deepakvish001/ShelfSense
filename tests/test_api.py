from fastapi.testclient import TestClient

from app.auth import APIKeyAuthenticator
from app.inventory import InventoryLedger
from app.main import create_app


def client(authenticator: APIKeyAuthenticator) -> TestClient:
    return TestClient(
        create_app(InventoryLedger(), authenticator=authenticator),
        headers={"X-API-Key": "admin-key"},
    )


def test_receipt_and_issue_update_stock_levels(authenticator) -> None:
    api = client(authenticator)
    receipt = api.post(
        "/api/v1/inventory/receipts",
        json={"reference": "PO-1", "sku": "soap", "quantity": 10},
    )
    issue = api.post(
        "/api/v1/inventory/issues",
        json={"reference": "SALE-1", "sku": "SOAP", "quantity": 4},
    )
    levels = api.get("/api/v1/inventory/levels")
    assert receipt.status_code == 201
    assert issue.status_code == 201
    assert levels.json() == {"SOAP": 6}


def test_overselling_returns_conflict(authenticator) -> None:
    response = client(authenticator).post(
        "/api/v1/inventory/issues",
        json={"reference": "SALE-1", "sku": "SOAP", "quantity": 1},
    )
    assert response.status_code == 409
    assert response.json()["detail"] == "insufficient stock"


def test_invalid_quantity_returns_validation_error(authenticator) -> None:
    response = client(authenticator).post(
        "/api/v1/inventory/receipts",
        json={"reference": "PO-1", "sku": "SOAP", "quantity": 0},
    )
    assert response.status_code == 422


def test_viewer_cannot_create_inventory_movement(authenticator) -> None:
    api = TestClient(
        create_app(InventoryLedger(), authenticator=authenticator),
        headers={"X-API-Key": "viewer-key"},
    )
    response = api.post(
        "/api/v1/inventory/receipts",
        json={"reference": "PO-1", "sku": "SOAP", "quantity": 1},
    )
    assert response.status_code == 403
