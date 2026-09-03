from collections.abc import Mapping
from typing import Protocol

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.inventory import StockMovement


class InventoryService(Protocol):
    @property
    def quantities(self) -> Mapping[str, int]: ...

    def receive(self, *, reference: str, sku: str, quantity: int) -> StockMovement: ...

    def issue(self, *, reference: str, sku: str, quantity: int) -> StockMovement: ...


class StockCommand(BaseModel):
    reference: str = Field(min_length=1, max_length=80)
    sku: str = Field(min_length=1, max_length=48)
    quantity: int = Field(gt=0)


class MovementResponse(BaseModel):
    reference: str
    sku: str
    movement_type: str
    quantity_delta: int
    occurred_at: str


def movement_response(movement: StockMovement) -> MovementResponse:
    return MovementResponse(
        reference=movement.reference,
        sku=movement.sku,
        movement_type=movement.movement_type.value,
        quantity_delta=movement.quantity_delta,
        occurred_at=movement.occurred_at.isoformat(),
    )


def create_inventory_router(ledger: InventoryService) -> APIRouter:
    router = APIRouter(prefix="/api/v1/inventory", tags=["inventory"])

    @router.post("/receipts", response_model=MovementResponse, status_code=status.HTTP_201_CREATED)
    def receive_stock(command: StockCommand) -> MovementResponse:
        try:
            movement = ledger.receive(**command.model_dump())
        except ValueError as error:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
        return movement_response(movement)

    @router.post("/issues", response_model=MovementResponse, status_code=status.HTTP_201_CREATED)
    def issue_stock(command: StockCommand) -> MovementResponse:
        try:
            movement = ledger.issue(**command.model_dump())
        except ValueError as error:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
        return movement_response(movement)

    @router.get("/levels", response_model=dict[str, int])
    def stock_levels() -> dict[str, int]:
        return dict(ledger.quantities)

    return router
