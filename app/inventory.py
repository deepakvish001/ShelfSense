from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from types import MappingProxyType
from typing import Mapping

from app.catalog import normalize_sku


class MovementType(StrEnum):
    RECEIPT = "receipt"
    ISSUE = "issue"
    ADJUSTMENT = "adjustment"


@dataclass(frozen=True, slots=True)
class StockMovement:
    reference: str
    sku: str
    movement_type: MovementType
    quantity_delta: int
    occurred_at: datetime


class InventoryLedger:
    def __init__(self) -> None:
        self._quantities: dict[str, int] = {}
        self._movements: dict[str, StockMovement] = {}

    @property
    def quantities(self) -> Mapping[str, int]:
        return MappingProxyType(self._quantities)

    @property
    def movements(self) -> tuple[StockMovement, ...]:
        return tuple(self._movements.values())

    def receive(self, *, reference: str, sku: str, quantity: int) -> StockMovement:
        if quantity <= 0:
            raise ValueError("quantity must be positive")
        return self._record(reference, sku, MovementType.RECEIPT, quantity)

    def issue(self, *, reference: str, sku: str, quantity: int) -> StockMovement:
        normalized_sku = normalize_sku(sku)
        if quantity <= 0:
            raise ValueError("quantity must be positive")
        if self._quantities.get(normalized_sku, 0) < quantity:
            raise ValueError("insufficient stock")
        return self._record(reference, normalized_sku, MovementType.ISSUE, -quantity)

    def _record(
        self,
        reference: str,
        sku: str,
        movement_type: MovementType,
        quantity_delta: int,
    ) -> StockMovement:
        normalized_reference = reference.strip()
        normalized_sku = normalize_sku(sku)
        if not normalized_reference:
            raise ValueError("reference is required")
        if normalized_reference in self._movements:
            raise ValueError("movement reference already exists")
        if quantity_delta == 0:
            raise ValueError("quantity cannot be zero")
        movement = StockMovement(
            reference=normalized_reference,
            sku=normalized_sku,
            movement_type=movement_type,
            quantity_delta=quantity_delta,
            occurred_at=datetime.now(UTC),
        )
        self._quantities[normalized_sku] = self._quantities.get(normalized_sku, 0) + quantity_delta
        self._movements[normalized_reference] = movement
        return movement
