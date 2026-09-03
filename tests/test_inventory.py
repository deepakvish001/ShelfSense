import pytest

from app.inventory import InventoryLedger, MovementType


def test_receipt_increases_available_stock() -> None:
    ledger = InventoryLedger()
    movement = ledger.receive(reference="PO-101", sku="milk 1l", quantity=20)
    assert movement.movement_type is MovementType.RECEIPT
    assert movement.quantity_delta == 20
    assert ledger.quantities["MILK-1L"] == 20


def test_issue_decreases_available_stock() -> None:
    ledger = InventoryLedger()
    ledger.receive(reference="PO-101", sku="SOAP", quantity=10)
    ledger.issue(reference="SALE-1", sku="soap", quantity=4)
    assert ledger.quantities["SOAP"] == 6


def test_issue_cannot_make_stock_negative() -> None:
    ledger = InventoryLedger()
    ledger.receive(reference="PO-101", sku="SOAP", quantity=2)
    with pytest.raises(ValueError, match="insufficient stock"):
        ledger.issue(reference="SALE-1", sku="SOAP", quantity=3)


def test_reference_is_idempotency_boundary() -> None:
    ledger = InventoryLedger()
    ledger.receive(reference="PO-101", sku="SOAP", quantity=2)
    with pytest.raises(ValueError, match="already exists"):
        ledger.receive(reference="PO-101", sku="SOAP", quantity=2)


def test_receipt_quantity_must_be_positive() -> None:
    ledger = InventoryLedger()
    with pytest.raises(ValueError, match="must be positive"):
        ledger.receive(reference="PO-101", sku="SOAP", quantity=0)
