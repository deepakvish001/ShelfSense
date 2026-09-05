from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from app.api import create_inventory_router
from app.audit_api import create_audit_router
from app.auth import APIKeyAuthenticator
from app.catalog_api import create_catalogue_router
from app.config import Environment, Settings
from app.inventory import InventoryLedger
from app.operations import OperationalHeadersMiddleware
from app.persistent_inventory import PersistentInventory
from app.reporting_api import create_reporting_router
from app.store import SQLiteStore
from app.suppliers_api import create_suppliers_router


def create_app(
    ledger: InventoryLedger | None = None,
    store: SQLiteStore | None = None,
    authenticator: APIKeyAuthenticator | None = None,
    settings: Settings | None = None,
) -> FastAPI:
    configuration = settings or Settings.from_environment()
    repository = store or SQLiteStore(configuration.database_path)
    repository.initialize()
    auth = authenticator or APIKeyAuthenticator.from_environment()
    application = FastAPI(title="ShelfSense API", version="1.0.0")
    application.add_middleware(
        OperationalHeadersMiddleware,
        production=configuration.environment is Environment.PRODUCTION,
    )
    if configuration.allowed_origins:
        application.add_middleware(
            CORSMiddleware,
            allow_origins=list(configuration.allowed_origins),
            allow_credentials=False,
            allow_methods=["GET", "POST"],
            allow_headers=["Content-Type", "X-API-Key", "X-Request-ID"],
        )
    inventory = ledger or PersistentInventory(repository)
    application.include_router(create_inventory_router(inventory, auth, repository))
    application.include_router(create_catalogue_router(repository, auth))
    application.include_router(create_suppliers_router(repository, auth))
    application.include_router(create_audit_router(repository, auth))
    application.include_router(create_reporting_router(repository, auth))

    @application.get("/healthz", tags=["system"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @application.get("/readyz", tags=["system"])
    def readiness() -> dict[str, str]:
        if not repository.ping():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="database unavailable",
            )
        return {"status": "ready"}

    return application


app = create_app()
