import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from app.audit import AuditEvent
from app.catalog import Product, normalize_sku
from app.inventory import MovementType, StockMovement
from app.suppliers import Supplier, normalize_supplier_code


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

                CREATE TABLE IF NOT EXISTS suppliers (
                    code TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT,
                    phone TEXT,
                    active INTEGER NOT NULL CHECK (active IN (0, 1)),
                    CHECK (email IS NOT NULL OR phone IS NOT NULL)
                );

                CREATE TABLE IF NOT EXISTS audit_events (
                    event_id TEXT PRIMARY KEY,
                    actor TEXT NOT NULL,
                    role TEXT NOT NULL,
                    action TEXT NOT NULL,
                    resource TEXT NOT NULL,
                    details_json TEXT NOT NULL,
                    occurred_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_audit_events_occurred_at
                ON audit_events (occurred_at DESC);
                """
            )

    def ping(self) -> bool:
        try:
            with self.connection() as connection:
                return connection.execute("SELECT 1").fetchone()[0] == 1
        except sqlite3.Error:
            return False

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

    def add_supplier(self, supplier: Supplier) -> None:
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO suppliers (code, name, email, phone, active)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    supplier.code,
                    supplier.name,
                    supplier.email,
                    supplier.phone,
                    int(supplier.active),
                ),
            )

    def get_supplier(self, code: str) -> Supplier | None:
        with self.connection() as connection:
            row = connection.execute(
                """SELECT code, name, email, phone, active FROM suppliers WHERE code = ?""",
                (normalize_supplier_code(code),),
            ).fetchone()
        if row is None:
            return None
        return Supplier(
            code=row["code"],
            name=row["name"],
            email=row["email"],
            phone=row["phone"],
            active=bool(row["active"]),
        )

    def list_suppliers(self, *, active_only: bool = False) -> list[Supplier]:
        query = "SELECT code, name, email, phone, active FROM suppliers"
        parameters: tuple[int, ...] = ()
        if active_only:
            query += " WHERE active = ?"
            parameters = (1,)
        query += " ORDER BY name, code"
        with self.connection() as connection:
            rows = connection.execute(query, parameters).fetchall()
        return [
            Supplier(
                code=row["code"],
                name=row["name"],
                email=row["email"],
                phone=row["phone"],
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

    def stock_levels(self) -> dict[str, int]:
        with self.connection() as connection:
            rows = connection.execute(
                """SELECT sku, SUM(quantity_delta) AS quantity
                FROM stock_movements GROUP BY sku ORDER BY sku"""
            ).fetchall()
        return {row["sku"]: int(row["quantity"]) for row in rows}

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

    def add_audit_event(self, event: AuditEvent) -> None:
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO audit_events
                    (event_id, actor, role, action, resource, details_json, occurred_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.event_id,
                    event.actor,
                    event.role,
                    event.action,
                    event.resource,
                    json.dumps(event.details, sort_keys=True, separators=(",", ":")),
                    event.occurred_at.isoformat(),
                ),
            )

    def list_audit_events(self, *, limit: int = 100) -> list[AuditEvent]:
        if not 1 <= limit <= 500:
            raise ValueError("audit limit must be between 1 and 500")
        with self.connection() as connection:
            rows = connection.execute(
                """SELECT event_id, actor, role, action, resource, details_json, occurred_at
                FROM audit_events ORDER BY occurred_at DESC, event_id DESC LIMIT ?""",
                (limit,),
            ).fetchall()
        return [
            AuditEvent(
                event_id=row["event_id"],
                actor=row["actor"],
                role=row["role"],
                action=row["action"],
                resource=row["resource"],
                details=json.loads(row["details_json"]),
                occurred_at=datetime.fromisoformat(row["occurred_at"]),
            )
            for row in rows
        ]
