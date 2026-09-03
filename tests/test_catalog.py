from decimal import Decimal

import pytest

from app.catalog import Product, normalize_sku


def test_sku_is_normalized_for_consistent_lookups() -> None:
    assert normalize_sku(" milk 1l ") == "MILK-1L"


def test_product_trims_display_fields() -> None:
    product = Product("soap-100", "  Hand Soap ", " Personal Care ", Decimal("35.00"))
    assert product.sku == "SOAP-100"
    assert product.name == "Hand Soap"
    assert product.category == "Personal Care"


@pytest.mark.parametrize("sku", ["", "milk/1l", "bad.sku"])
def test_invalid_sku_is_rejected(sku: str) -> None:
    with pytest.raises(ValueError):
        normalize_sku(sku)


def test_negative_selling_price_is_rejected() -> None:
    with pytest.raises(ValueError, match="cannot be negative"):
        Product("SOAP", "Soap", "Care", Decimal("-0.01"))
