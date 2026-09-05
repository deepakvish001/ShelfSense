import sqlite3
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.auth import APIKeyAuthenticator, Role
from app.catalog import Product
from app.store import SQLiteStore


class ProductCreate(BaseModel):
    sku: str = Field(min_length=1, max_length=48)
    name: str = Field(min_length=1, max_length=160)
    category: str = Field(min_length=1, max_length=100)
    selling_price: Decimal = Field(ge=0, max_digits=14, decimal_places=2)
    active: bool = True


class ProductResponse(BaseModel):
    sku: str
    name: str
    category: str
    selling_price: Decimal
    active: bool


def product_response(product: Product) -> ProductResponse:
    return ProductResponse(
        sku=product.sku,
        name=product.name,
        category=product.category,
        selling_price=product.selling_price,
        active=product.active,
    )


def create_catalogue_router(store: SQLiteStore, authenticator: APIKeyAuthenticator) -> APIRouter:
    router = APIRouter(prefix="/api/v1/products", tags=["catalogue"])

    @router.post(
        "",
        response_model=ProductResponse,
        status_code=status.HTTP_201_CREATED,
        dependencies=[Depends(authenticator.require(Role.OPERATOR, Role.ADMIN))],
    )
    def create_product(command: ProductCreate) -> ProductResponse:
        try:
            product = Product(**command.model_dump())
            store.add_product(product)
        except sqlite3.IntegrityError as error:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="product SKU already exists",
            ) from error
        except ValueError as error:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=str(error),
            ) from error
        return product_response(product)

    @router.get(
        "",
        response_model=list[ProductResponse],
        dependencies=[Depends(authenticator.require(Role.VIEWER, Role.OPERATOR, Role.ADMIN))],
    )
    def list_products(active_only: bool = Query(default=False)) -> list[ProductResponse]:
        return [
            product_response(product)
            for product in store.list_products(active_only=active_only)
        ]

    @router.get(
        "/{sku}",
        response_model=ProductResponse,
        dependencies=[Depends(authenticator.require(Role.VIEWER, Role.OPERATOR, Role.ADMIN))],
    )
    def get_product(sku: str) -> ProductResponse:
        product = store.get_product(sku)
        if product is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="product not found",
            )
        return product_response(product)

    return router
