from dataclasses import dataclass
from decimal import Decimal


def normalize_sku(value: str) -> str:
    normalized = value.strip().upper().replace(" ", "-")
    if not normalized:
        raise ValueError("sku is required")
    if len(normalized) > 48:
        raise ValueError("sku cannot exceed 48 characters")
    if not all(character.isalnum() or character in {"-", "_"} for character in normalized):
        raise ValueError("sku contains unsupported characters")
    return normalized


@dataclass(frozen=True, slots=True)
class Product:
    sku: str
    name: str
    category: str
    selling_price: Decimal
    active: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "sku", normalize_sku(self.sku))
        object.__setattr__(self, "name", self.name.strip())
        object.__setattr__(self, "category", self.category.strip())
        if not self.name:
            raise ValueError("product name is required")
        if not self.category:
            raise ValueError("category is required")
        if self.selling_price < 0:
            raise ValueError("selling price cannot be negative")
