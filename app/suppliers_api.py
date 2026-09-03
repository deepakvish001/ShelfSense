import sqlite3

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.store import SQLiteStore
from app.suppliers import Supplier


class SupplierCreate(BaseModel):
    code: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=160)
    email: str | None = Field(default=None, max_length=254)
    phone: str | None = Field(default=None, max_length=32)
    active: bool = True


class SupplierResponse(BaseModel):
    code: str
    name: str
    email: str | None
    phone: str | None
    active: bool


def supplier_response(supplier: Supplier) -> SupplierResponse:
    return SupplierResponse(
        code=supplier.code,
        name=supplier.name,
        email=supplier.email,
        phone=supplier.phone,
        active=supplier.active,
    )


def create_suppliers_router(store: SQLiteStore) -> APIRouter:
    router = APIRouter(prefix="/api/v1/suppliers", tags=["suppliers"])

    @router.post("", response_model=SupplierResponse, status_code=status.HTTP_201_CREATED)
    def create_supplier(command: SupplierCreate) -> SupplierResponse:
        try:
            supplier = Supplier(**command.model_dump())
            store.add_supplier(supplier)
        except sqlite3.IntegrityError as error:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="supplier code already exists",
            ) from error
        except ValueError as error:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=str(error),
            ) from error
        return supplier_response(supplier)

    @router.get("", response_model=list[SupplierResponse])
    def list_suppliers(active_only: bool = Query(default=False)) -> list[SupplierResponse]:
        return [
            supplier_response(supplier)
            for supplier in store.list_suppliers(active_only=active_only)
        ]

    @router.get("/{code}", response_model=SupplierResponse)
    def get_supplier(code: str) -> SupplierResponse:
        supplier = store.get_supplier(code)
        if supplier is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="supplier not found",
            )
        return supplier_response(supplier)

    return router
