from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.catalog import Product
from app.inventory import MovementType, StockMovement
from app.store import DuplicateReferenceError, SQLiteStore


@pytest.fixture
def store(tmp_path) -> SQLiteStore:
    repository = SQLiteStore(tmp_path / "inventory.db")
    repository.initialize()
    return repository


def test_product_survives_repository_reopen(store: SQLiteStore) -> None:
    store.add_product(Product("soap", "Hand Soap", "Care", Decimal("35.00")))
    reopened = SQLiteStore(store.database_path)
    assert reopened.get_product("SOAP") == Product(
        "SOAP", "Hand Soap", "Care", Decimal("35.00")
    )


def test_active_product_filter_excludes_inactive_records(store: SQLiteStore) -> None:
    store.add_product(Product("SOAP", "Soap", "Care", Decimal(35)))
    store.add_product(Product("OLD", "Legacy", "Care", Decimal(20), active=False))
    assert [product.sku for product in store.list_products(active_only=True)] == ["SOAP"]


def test_movements_are_summed_into_current_stock(store: SQLiteStore) -> None:
    now = datetime.now(UTC)
    store.add_movement(StockMovement("PO-1", "SOAP", MovementType.RECEIPT, 10, now))
    store.add_movement(StockMovement("SALE-1", "SOAP", MovementType.ISSUE, -4, now))
    assert store.stock_level("soap") == 6
    assert [movement.reference for movement in store.list_movements("SOAP")] == [
        "PO-1",
        "SALE-1",
    ]


def test_duplicate_movement_reference_is_rejected(store: SQLiteStore) -> None:
    movement = StockMovement(
        "PO-1", "SOAP", MovementType.RECEIPT, 10, datetime.now(UTC)
    )
    store.add_movement(movement)
    with pytest.raises(DuplicateReferenceError, match="already exists"):
        store.add_movement(movement)
