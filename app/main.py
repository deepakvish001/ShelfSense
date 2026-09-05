import os

from fastapi import FastAPI

from app.api import create_inventory_router
from app.audit_api import create_audit_router
from app.auth import APIKeyAuthenticator
from app.catalog_api import create_catalogue_router
from app.inventory import InventoryLedger
from app.persistent_inventory import PersistentInventory
from app.store import SQLiteStore
from app.suppliers_api import create_suppliers_router


def create_app(
    ledger: InventoryLedger | None = None,
    store: SQLiteStore | None = None,
    authenticator: APIKeyAuthenticator | None = None,
) -> FastAPI:
    repository = store or SQLiteStore(os.getenv("DATABASE_PATH", "shelfsense.db"))
    repository.initialize()
    auth = authenticator or APIKeyAuthenticator.from_environment()
    application = FastAPI(title="ShelfSense API", version="0.1.0")
    inventory = ledger or PersistentInventory(repository)
    application.include_router(create_inventory_router(inventory, auth, repository))
    application.include_router(create_catalogue_router(repository, auth))
    application.include_router(create_suppliers_router(repository, auth))
    application.include_router(create_audit_router(repository, auth))

    @application.get("/healthz", tags=["system"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return application


app = create_app()
