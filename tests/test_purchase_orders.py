from decimal import Decimal

import pytest

from app.purchase_orders import PurchaseOrder, PurchaseOrderLine, PurchaseOrderStatus


def order() -> PurchaseOrder:
    return PurchaseOrder(
        reference=" po-101 ",
        supplier_code="fresh foods",
        lines=(
            PurchaseOrderLine("milk 1l", 10, Decimal("42.50")),
            PurchaseOrderLine("bread", 5, Decimal(25)),
        ),
    )


def test_purchase_order_normalizes_identity_and_calculates_total() -> None:
    purchase_order = order()
    assert purchase_order.reference == "PO-101"
    assert purchase_order.supplier_code == "FRESH-FOODS"
    assert purchase_order.total == Decimal("550.00")


def test_purchase_order_moves_through_submit_and_receive() -> None:
    submitted = order().submit()
    received = submitted.receive()
    assert submitted.status is PurchaseOrderStatus.SUBMITTED
    assert received.status is PurchaseOrderStatus.RECEIVED


def test_received_purchase_order_cannot_be_cancelled() -> None:
    with pytest.raises(ValueError, match="cannot cancel"):
        order().submit().receive().cancel()


def test_draft_purchase_order_cannot_be_received() -> None:
    with pytest.raises(ValueError, match="expected submitted"):
        order().receive()


def test_duplicate_sku_lines_are_rejected() -> None:
    with pytest.raises(ValueError, match="duplicate SKUs"):
        PurchaseOrder(
            reference="PO-1",
            supplier_code="LOCAL",
            lines=(
                PurchaseOrderLine("SOAP", 1, Decimal(10)),
                PurchaseOrderLine("soap", 2, Decimal(10)),
            ),
        )
