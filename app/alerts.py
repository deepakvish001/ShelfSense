from dataclasses import dataclass
from datetime import date
from enum import StrEnum

from app.domain import StockBatch


class AlertKind(StrEnum):
    LOW_STOCK = "low_stock"
    EXPIRING = "expiring"
    EXPIRED = "expired"


@dataclass(frozen=True, slots=True)
class InventoryAlert:
    sku: str
    kind: AlertKind
    message: str


def stock_alerts(
    batches: list[StockBatch],
    *,
    today: date,
    expiry_window_days: int = 30,
) -> list[InventoryAlert]:
    if expiry_window_days < 0:
        raise ValueError("expiry window cannot be negative")
    alerts: list[InventoryAlert] = []
    for batch in batches:
        if batch.needs_reorder():
            alerts.append(
                InventoryAlert(
                    sku=batch.sku,
                    kind=AlertKind.LOW_STOCK,
                    message=f"{batch.sku} has {batch.quantity} units remaining",
                )
            )
        if batch.expires_on is None:
            continue
        if batch.expires_on < today:
            alerts.append(
                InventoryAlert(
                    sku=batch.sku,
                    kind=AlertKind.EXPIRED,
                    message=f"{batch.sku} expired on {batch.expires_on.isoformat()}",
                )
            )
        elif batch.expires_within(expiry_window_days, today=today):
            alerts.append(
                InventoryAlert(
                    sku=batch.sku,
                    kind=AlertKind.EXPIRING,
                    message=f"{batch.sku} expires on {batch.expires_on.isoformat()}",
                )
            )
    return alerts
