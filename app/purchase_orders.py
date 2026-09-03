from dataclasses import dataclass, replace
from decimal import Decimal
from enum import StrEnum

from app.catalog import normalize_sku
from app.suppliers import normalize_supplier_code


class PurchaseOrderStatus(StrEnum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    RECEIVED = "received"
    CANCELLED = "cancelled"


@dataclass(frozen=True, slots=True)
class PurchaseOrderLine:
    sku: str
    quantity: int
    unit_cost: Decimal

    def __post_init__(self) -> None:
        object.__setattr__(self, "sku", normalize_sku(self.sku))
        if self.quantity <= 0:
            raise ValueError("line quantity must be positive")
        if self.unit_cost < 0:
            raise ValueError("line unit cost cannot be negative")

    @property
    def total(self) -> Decimal:
        return self.unit_cost * self.quantity


@dataclass(frozen=True, slots=True)
class PurchaseOrder:
    reference: str
    supplier_code: str
    lines: tuple[PurchaseOrderLine, ...]
    status: PurchaseOrderStatus = PurchaseOrderStatus.DRAFT

    def __post_init__(self) -> None:
        object.__setattr__(self, "reference", self.reference.strip().upper())
        object.__setattr__(self, "supplier_code", normalize_supplier_code(self.supplier_code))
        if not self.reference:
            raise ValueError("purchase order reference is required")
        if not self.lines:
            raise ValueError("purchase order requires at least one line")
        if len({line.sku for line in self.lines}) != len(self.lines):
            raise ValueError("purchase order cannot contain duplicate SKUs")

    @property
    def total(self) -> Decimal:
        return sum((line.total for line in self.lines), start=Decimal(0))

    def submit(self) -> "PurchaseOrder":
        self._require_status(PurchaseOrderStatus.DRAFT)
        return replace(self, status=PurchaseOrderStatus.SUBMITTED)

    def receive(self) -> "PurchaseOrder":
        self._require_status(PurchaseOrderStatus.SUBMITTED)
        return replace(self, status=PurchaseOrderStatus.RECEIVED)

    def cancel(self) -> "PurchaseOrder":
        if self.status not in {PurchaseOrderStatus.DRAFT, PurchaseOrderStatus.SUBMITTED}:
            raise ValueError(f"cannot cancel purchase order in {self.status} status")
        return replace(self, status=PurchaseOrderStatus.CANCELLED)

    def _require_status(self, expected: PurchaseOrderStatus) -> None:
        if self.status is not expected:
            raise ValueError(f"expected {expected} purchase order, found {self.status}")
