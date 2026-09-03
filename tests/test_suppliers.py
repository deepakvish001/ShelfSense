import pytest

from app.suppliers import Supplier, normalize_supplier_code


def test_supplier_fields_are_normalized() -> None:
    supplier = Supplier(
        code=" fresh foods ",
        name=" Fresh Foods Ltd ",
        email=" ORDERS@EXAMPLE.COM ",
    )
    assert supplier.code == "FRESH-FOODS"
    assert supplier.name == "Fresh Foods Ltd"
    assert supplier.email == "orders@example.com"


def test_supplier_requires_contact_method() -> None:
    with pytest.raises(ValueError, match="email or phone"):
        Supplier(code="LOCAL", name="Local Supplier")


@pytest.mark.parametrize("code", ["", "bad/code", "bad.code"])
def test_invalid_supplier_code_is_rejected(code: str) -> None:
    with pytest.raises(ValueError):
        normalize_supplier_code(code)


def test_invalid_phone_is_rejected() -> None:
    with pytest.raises(ValueError, match="phone is invalid"):
        Supplier(code="LOCAL", name="Local Supplier", phone="call-me")


def test_invalid_email_is_rejected() -> None:
    with pytest.raises(ValueError, match="email is invalid"):
        Supplier(code="LOCAL", name="Local Supplier", email="not-an-email")
