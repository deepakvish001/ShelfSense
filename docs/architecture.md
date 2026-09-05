# Architecture

ShelfSense follows a small layered design so business rules can evolve independently from HTTP and persistence concerns.

## Layers

1. **Domain** — products, suppliers, stock batches, movements, alerts, and purchase-order transitions.
2. **Application services** — inventory commands and reporting calculations.
3. **Transport** — versioned FastAPI routers, validation, authentication, and response contracts.
4. **Persistence** — transactional SQLite access for catalogue, suppliers, movements, and audit events.
5. **Operations** — settings, request correlation, security headers, health probes, containers, and CI.

## Important invariants

- Stock issues cannot reduce an SKU below zero.
- Movement references are unique and serve as an idempotency boundary.
- Money uses decimal values rather than binary floating point.
- Purchase-order transitions return new immutable values.
- Protected writes record actor and role in the audit feed.
- Production cannot start without explicit API-key configuration.

## Data ownership

The SQLite database is authoritative for products, suppliers, movements, and audit events. Current stock is calculated from the append-only movement ledger rather than stored as a mutable counter. This keeps every quantity explainable.

## Scaling path

For multi-instance deployments, implement the repository behavior with PostgreSQL, add transaction-level row locking around stock issues, move credentials to an external identity provider, and publish audit events to durable object storage or a security event platform. Domain and HTTP contracts can remain stable while those adapters change.
