from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.catalog import Product
from app.inventory import InventoryLedger
from app.main import create_app
from app.store import SQLiteStore


@pytest.fixture
def api(tmp_path, authenticator, admin_headers) -> TestClient:
    store = SQLiteStore(tmp_path / "catalogue.db")
    return TestClient(
        create_app(InventoryLedger(), store, authenticator),
        headers=admin_headers,
    )


def test_create_and_read_product(api: TestClient) -> None:
    created = api.post(
        "/api/v1/products",
        json={
            "sku": "milk 1l",
            "name": "Full Cream Milk",
            "category": "Dairy",
            "selling_price": "64.50",
        },
    )
    fetched = api.get("/api/v1/products/MILK-1L")
    assert created.status_code == 201
    assert fetched.status_code == 200
    assert fetched.json()["sku"] == "MILK-1L"
    assert fetched.json()["selling_price"] == "64.50"


def test_duplicate_sku_returns_conflict(api: TestClient) -> None:
    command = {
        "sku": "SOAP",
        "name": "Soap",
        "category": "Care",
        "selling_price": "35.00",
    }
    assert api.post("/api/v1/products", json=command).status_code == 201
    response = api.post("/api/v1/products", json=command)
    assert response.status_code == 409


def test_active_filter_hides_inactive_products(
    api: TestClient,
    tmp_path,
    authenticator,
    admin_headers,
) -> None:
    store = SQLiteStore(tmp_path / "filter.db")
    store.initialize()
    store.add_product(Product("LIVE", "Live", "Demo", Decimal(1)))
    store.add_product(Product("OLD", "Old", "Demo", Decimal(1), active=False))
    filtered_api = TestClient(
        create_app(InventoryLedger(), store, authenticator),
        headers=admin_headers,
    )
    response = filtered_api.get("/api/v1/products?active_only=true")
    assert [product["sku"] for product in response.json()] == ["LIVE"]


def test_unknown_product_returns_not_found(api: TestClient) -> None:
    response = api.get("/api/v1/products/UNKNOWN")
    assert response.status_code == 404
