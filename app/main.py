import os

from fastapi import FastAPI

from app.api import create_inventory_router
from app.catalog_api import create_catalogue_router
from app.inventory import InventoryLedger
from app.store import SQLiteStore


def create_app(
    ledger: InventoryLedger | None = None,
    store: SQLiteStore | None = None,
) -> FastAPI:
    repository = store or SQLiteStore(os.getenv("DATABASE_PATH", "shelfsense.db"))
    repository.initialize()
    application = FastAPI(title="ShelfSense API", version="0.1.0")
    application.include_router(create_inventory_router(ledger or InventoryLedger()))
    application.include_router(create_catalogue_router(repository))

    @application.get("/healthz", tags=["system"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return application


app = create_app()
