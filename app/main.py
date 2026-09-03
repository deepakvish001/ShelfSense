from fastapi import FastAPI

from app.api import create_inventory_router
from app.inventory import InventoryLedger


def create_app(ledger: InventoryLedger | None = None) -> FastAPI:
    application = FastAPI(title="ShelfSense API", version="0.1.0")
    application.include_router(create_inventory_router(ledger or InventoryLedger()))

    @application.get("/healthz", tags=["system"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return application


app = create_app()
