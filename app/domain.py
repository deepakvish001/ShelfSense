from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class StockBatch:
    sku: str
    quantity: int
    reorder_level: int
    expires_on: date | None = None
    unit_cost: Decimal = Decimal(0)

    def __post_init__(self) -> None:
        if not self.sku.strip():
            raise ValueError("sku is required")
        if self.quantity < 0 or self.reorder_level < 0:
            raise ValueError("stock values cannot be negative")
        if self.unit_cost < 0:
            raise ValueError("unit cost cannot be negative")

    def needs_reorder(self) -> bool:
        return self.quantity <= self.reorder_level

    def expires_within(self, days: int, *, today: date | None = None) -> bool:
        if days < 0:
            raise ValueError("days cannot be negative")
        if self.expires_on is None:
            return False
        anchor = today or datetime.now(UTC).date()
        return anchor <= self.expires_on <= date.fromordinal(anchor.toordinal() + days)
