import pytest

from app.persistent_inventory import PersistentInventory
from app.store import DuplicateReferenceError, SQLiteStore


@pytest.fixture
def service(tmp_path) -> PersistentInventory:
    store = SQLiteStore(tmp_path / "durable.db")
    store.initialize()
    return PersistentInventory(store)


def test_stock_survives_service_recreation(service: PersistentInventory) -> None:
    service.receive(reference="PO-1", sku="SOAP", quantity=10)
    recreated = PersistentInventory(SQLiteStore(service.store.database_path))
    assert recreated.quantities == {"SOAP": 10}


def test_durable_issue_protects_against_overselling(service: PersistentInventory) -> None:
    service.receive(reference="PO-1", sku="SOAP", quantity=2)
    with pytest.raises(ValueError, match="insufficient stock"):
        service.issue(reference="SALE-1", sku="SOAP", quantity=3)
    assert service.quantities == {"SOAP": 2}


def test_duplicate_reference_remains_rejected_after_recreation(
    service: PersistentInventory,
) -> None:
    service.receive(reference="PO-1", sku="SOAP", quantity=2)
    recreated = PersistentInventory(SQLiteStore(service.store.database_path))
    with pytest.raises(DuplicateReferenceError, match="already exists"):
        recreated.receive(reference="PO-1", sku="SOAP", quantity=2)
