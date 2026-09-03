from datetime import date

import pytest

from app.alerts import AlertKind, stock_alerts
from app.domain import StockBatch


def test_low_stock_and_expiry_alerts_can_coexist() -> None:
    alerts = stock_alerts(
        [StockBatch("MILK", quantity=2, reorder_level=5, expires_on=date(2026, 9, 8))],
        today=date(2026, 9, 3),
        expiry_window_days=7,
    )
    assert [alert.kind for alert in alerts] == [AlertKind.LOW_STOCK, AlertKind.EXPIRING]


def test_expired_batch_is_not_reported_as_merely_expiring() -> None:
    alerts = stock_alerts(
        [StockBatch("YOGURT", quantity=10, reorder_level=2, expires_on=date(2026, 9, 2))],
        today=date(2026, 9, 3),
    )
    assert [alert.kind for alert in alerts] == [AlertKind.EXPIRED]


def test_healthy_batch_produces_no_alert() -> None:
    alerts = stock_alerts(
        [StockBatch("SOAP", quantity=20, reorder_level=5)],
        today=date(2026, 9, 3),
    )
    assert alerts == []


def test_negative_expiry_window_is_rejected() -> None:
    with pytest.raises(ValueError, match="cannot be negative"):
        stock_alerts([], today=date(2026, 9, 3), expiry_window_days=-1)
