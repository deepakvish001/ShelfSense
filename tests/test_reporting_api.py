from datetime import UTC, datetime
from decimal import Decimal

from fastapi.testclient import TestClient

from app.catalog import Product
from app.inventory import InventoryLedger, MovementType, StockMovement
from app.main import create_app
from app.store import SQLiteStore


def test_summary_and_csv_are_available_to_viewer(tmp_path, authenticator) -> None:
    store = SQLiteStore(tmp_path / "api-reporting.db")
    store.initialize()
    store.add_product(Product("SOAP", "Soap", "Care", Decimal(35)))
    store.add_movement(
        StockMovement("PO-1", "SOAP", MovementType.RECEIPT, 3, datetime.now(UTC))
    )
    api = TestClient(
        create_app(InventoryLedger(), store, authenticator),
        headers={"X-API-Key": "viewer-key"},
    )
    summary = api.get("/api/v1/reports/inventory-summary")
    export = api.get("/api/v1/reports/inventory.csv")
    assert summary.status_code == 200
    assert summary.json()["total_units"] == 3
    assert export.status_code == 200
    assert export.headers["content-type"].startswith("text/csv")
    assert "SOAP,Soap,Care,true,3,35" in export.text
