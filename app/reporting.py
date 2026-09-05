import csv
from dataclasses import dataclass
from decimal import Decimal
from io import StringIO

from app.store import SQLiteStore


@dataclass(frozen=True, slots=True)
class InventorySummary:
    product_count: int
    active_product_count: int
    stocked_sku_count: int
    total_units: int
    retail_stock_value: Decimal


def inventory_summary(store: SQLiteStore) -> InventorySummary:
    products = store.list_products()
    levels = store.stock_levels()
    prices = {product.sku: product.selling_price for product in products}
    return InventorySummary(
        product_count=len(products),
        active_product_count=sum(product.active for product in products),
        stocked_sku_count=sum(quantity > 0 for quantity in levels.values()),
        total_units=sum(levels.values()),
        retail_stock_value=sum(
            (prices.get(sku, Decimal(0)) * quantity for sku, quantity in levels.items()),
            start=Decimal(0),
        ),
    )


def inventory_csv(store: SQLiteStore) -> str:
    output = StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(["sku", "name", "category", "active", "quantity", "selling_price"])
    levels = store.stock_levels()
    for product in store.list_products():
        writer.writerow(
            [
                product.sku,
                product.name,
                product.category,
                str(product.active).lower(),
                levels.get(product.sku, 0),
                str(product.selling_price),
            ]
        )
    return output.getvalue()
