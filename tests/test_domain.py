from datetime import date
from decimal import Decimal

import pytest

from app.domain import StockBatch


def test_batch_at_threshold_needs_reorder() -> None:
    batch = StockBatch("MILK-1L", 5, 5, unit_cost=Decimal("42.50"))
    assert batch.needs_reorder() is True


def test_expiry_window_is_inclusive() -> None:
    batch = StockBatch("YOGURT", 12, 3, expires_on=date(2026, 9, 10))
    assert batch.expires_within(7, today=date(2026, 9, 3)) is True


def test_negative_quantity_is_rejected() -> None:
    with pytest.raises(ValueError, match="cannot be negative"):
        StockBatch("SOAP", -1, 2)
