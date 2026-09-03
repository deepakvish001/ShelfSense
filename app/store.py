import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from app.catalog import Product, normalize_sku
from app.inventory import MovementType, StockMovement


class DuplicateReferenceError(ValueError):
    """Raised when an inventory movement reference has already been recorded."""


class SQLiteStore:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = str(database_path)

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def initialize(self) -> None:
        with self.connection() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS products (
                    sku TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    selling_price TEXT NOT NULL,
                    active INTEGER NOT NULL CHECK (active IN (0, 1))
                );

                CREATE TABLE IF NOT EXISTS stock_movements (
                    reference TEXT PRIMARY KEY,
                    sku TEXT NOT NULL,
                    movement_type TEXT NOT NULL,
                    quantity_delta INTEGER NOT NULL CHECK (quantity_delta <> 0),
                    occurred_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_stock_movements_sku
                ON stock_movements (sku, occurred_at);
                """
            )

    def add_product(self, product: Product) -> None:
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO products (sku, name, category, selling_price, active)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    product.sku,
                    product.name,
                    product.category,
                    str(product.selling_price),
                    int(product.active),
                ),
            )

    def get_product(self, sku: str) -> Product | None:
        with self.connection() as connection:
            row = connection.execute(
                """SELECT sku, name, category, selling_price, active FROM products WHERE sku = ?""",
                (normalize_sku(sku),),
            ).fetchone()
        if row is None:
            return None
        return Product(
            sku=row["sku"],
            name=row["name"],
            category=row["category"],
            selling_price=Decimal(row["selling_price"]),
            active=bool(row["active"]),
        )

    def list_products(self, *, active_only: bool = False) -> list[Product]:
        query = "SELECT sku, name, category, selling_price, active FROM products"
        parameters: tuple[int, ...] = ()
        if active_only:
            query += " WHERE active = ?"
            parameters = (1,)
        query += " ORDER BY name, sku"
        with self.connection() as connection:
            rows = connection.execute(query, parameters).fetchall()
        return [
            Product(
                sku=row["sku"],
                name=row["name"],
                category=row["category"],
                selling_price=Decimal(row["selling_price"]),
                active=bool(row["active"]),
            )
            for row in rows
        ]

    def add_movement(self, movement: StockMovement) -> None:
        try:
            with self.connection() as connection:
                connection.execute(
                    """
                    INSERT INTO stock_movements
                        (reference, sku, movement_type, quantity_delta, occurred_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        movement.reference,
                        movement.sku,
                        movement.movement_type.value,
                        movement.quantity_delta,
                        movement.occurred_at.isoformat(),
                    ),
                )
        except sqlite3.IntegrityError as error:
            raise DuplicateReferenceError("movement reference already exists") from error

    def stock_level(self, sku: str) -> int:
        with self.connection() as connection:
            row = connection.execute(
                """SELECT COALESCE(SUM(quantity_delta), 0) AS quantity
                FROM stock_movements WHERE sku = ?""",
                (normalize_sku(sku),),
            ).fetchone()
        return int(row["quantity"])

    def list_movements(self, sku: str) -> list[StockMovement]:
        with self.connection() as connection:
            rows = connection.execute(
                """SELECT reference, sku, movement_type, quantity_delta, occurred_at
                FROM stock_movements WHERE sku = ? ORDER BY occurred_at, reference""",
                (normalize_sku(sku),),
            ).fetchall()
        return [
            StockMovement(
                reference=row["reference"],
                sku=row["sku"],
                movement_type=MovementType(row["movement_type"]),
                quantity_delta=row["quantity_delta"],
                occurred_at=datetime.fromisoformat(row["occurred_at"]),
            )
            for row in rows
        ]
