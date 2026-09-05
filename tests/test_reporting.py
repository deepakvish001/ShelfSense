import csv
from datetime import UTC, datetime
from decimal import Decimal
from io import StringIO

from app.catalog import Product
from app.inventory import MovementType, StockMovement
from app.reporting import inventory_csv, inventory_summary
from app.store import SQLiteStore


def populated_store(tmp_path) -> SQLiteStore:
    store = SQLiteStore(tmp_path / "reporting.db")
    store.initialize()
    store.add_product(Product("SOAP", "Soap", "Care", Decimal("35.50")))
    store.add_product(Product("OLD", "Old Item", "Care", Decimal(10), active=False))
    store.add_movement(
        StockMovement("PO-1", "SOAP", MovementType.RECEIPT, 4, datetime.now(UTC))
    )
    return store


def test_inventory_summary_calculates_counts_units_and_value(tmp_path) -> None:
    report = inventory_summary(populated_store(tmp_path))
    assert report.product_count == 2
    assert report.active_product_count == 1
    assert report.stocked_sku_count == 1
    assert report.total_units == 4
    assert report.retail_stock_value == Decimal("142.00")


def test_inventory_csv_has_stable_headers_and_rows(tmp_path) -> None:
    rows = list(csv.DictReader(StringIO(inventory_csv(populated_store(tmp_path)))))
    assert list(rows[0]) == [
        "sku",
        "name",
        "category",
        "active",
        "quantity",
        "selling_price",
    ]
    soap = next(row for row in rows if row["sku"] == "SOAP")
    assert soap["quantity"] == "4"
    assert soap["selling_price"] == "35.50"
