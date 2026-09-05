from decimal import Decimal

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel

from app.auth import APIKeyAuthenticator, Role
from app.reporting import inventory_csv, inventory_summary
from app.store import SQLiteStore


class InventorySummaryResponse(BaseModel):
    product_count: int
    active_product_count: int
    stocked_sku_count: int
    total_units: int
    retail_stock_value: Decimal


def create_reporting_router(store: SQLiteStore, authenticator: APIKeyAuthenticator) -> APIRouter:
    router = APIRouter(
        prefix="/api/v1/reports",
        tags=["reports"],
        dependencies=[Depends(authenticator.require(Role.VIEWER, Role.OPERATOR, Role.ADMIN))],
    )

    @router.get("/inventory-summary", response_model=InventorySummaryResponse)
    def summary() -> InventorySummaryResponse:
        report = inventory_summary(store)
        return InventorySummaryResponse(
            product_count=report.product_count,
            active_product_count=report.active_product_count,
            stocked_sku_count=report.stocked_sku_count,
            total_units=report.total_units,
            retail_stock_value=report.retail_stock_value,
        )

    @router.get("/inventory.csv", response_class=Response)
    def export_inventory() -> Response:
        return Response(
            content=inventory_csv(store),
            media_type="text/csv",
            headers={"Content-Disposition": 'attachment; filename="inventory.csv"'},
        )

    return router
