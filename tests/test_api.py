from fastapi.testclient import TestClient

from app.inventory import InventoryLedger
from app.main import create_app


def client() -> TestClient:
    return TestClient(create_app(InventoryLedger()))


def test_receipt_and_issue_update_stock_levels() -> None:
    api = client()
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


def test_overselling_returns_conflict() -> None:
    response = client().post(
        "/api/v1/inventory/issues",
        json={"reference": "SALE-1", "sku": "SOAP", "quantity": 1},
    )
    assert response.status_code == 409
    assert response.json()["detail"] == "insufficient stock"


def test_invalid_quantity_returns_validation_error() -> None:
    response = client().post(
        "/api/v1/inventory/receipts",
        json={"reference": "PO-1", "sku": "SOAP", "quantity": 0},
    )
    assert response.status_code == 422
