from collections.abc import Mapping
from datetime import UTC, datetime
from types import MappingProxyType

from app.catalog import normalize_sku
from app.inventory import MovementType, StockMovement
from app.store import SQLiteStore


class PersistentInventory:
    def __init__(self, store: SQLiteStore) -> None:
        self.store = store

    @property
    def quantities(self) -> Mapping[str, int]:
        return MappingProxyType(self.store.stock_levels())

    def receive(self, *, reference: str, sku: str, quantity: int) -> StockMovement:
        if quantity <= 0:
            raise ValueError("quantity must be positive")
        return self._record(reference, sku, MovementType.RECEIPT, quantity)

    def issue(self, *, reference: str, sku: str, quantity: int) -> StockMovement:
        normalized_sku = normalize_sku(sku)
        if quantity <= 0:
            raise ValueError("quantity must be positive")
        if self.store.stock_level(normalized_sku) < quantity:
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
        if not normalized_reference:
            raise ValueError("reference is required")
        movement = StockMovement(
            reference=normalized_reference,
            sku=normalize_sku(sku),
            movement_type=movement_type,
            quantity_delta=quantity_delta,
            occurred_at=datetime.now(UTC),
        )
        self.store.add_movement(movement)
        return movement
