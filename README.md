# ShelfSense

Inventory intelligence API for small retailers, pharmacies, and local warehouses.

[![CI](https://github.com/deepakvish001/ShelfSense/actions/workflows/ci.yml/badge.svg)](https://github.com/deepakvish001/ShelfSense/actions/workflows/ci.yml)

ShelfSense provides a traceable product catalogue, supplier directory, stock movement ledger, purchase-order rules, inventory alerts, audit history, and operational reports. It targets a single location while keeping clear boundaries for future PostgreSQL and multi-location adapters.

## Highlights

- Normalized product and supplier identities
- Durable receipt and issue ledger with overselling protection
- Duplicate-reference protection for idempotent stock operations
- Product and supplier REST APIs
- Viewer, operator, and administrator authorization
- Append-only audit events for protected writes
- Inventory summary and deterministic CSV export
- Low-stock, expiring, and expired batch rules
- Immutable purchase-order lifecycle rules
- Liveness, database readiness, request IDs, CORS, and security headers
- Non-root, read-only container deployment with a persistent data volume
- Automated lint, test, and Docker build checks

## Technology

- Python 3.12
- FastAPI and Pydantic
- SQLite with transactional repository boundaries
- Pytest and Ruff
- Docker Compose
- GitHub Actions

## Quick start

### Local Python

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
export API_KEYS="$(python -c 'import secrets; print(secrets.token_urlsafe(32))'):admin:local-admin"
uvicorn app.main:app --reload
```

Open `http://localhost:8000/docs`. Send the generated secret through the `X-API-Key` header.

### Docker Compose

```bash
export SHELFSENSE_API_KEYS="$(python -c 'import secrets; print(secrets.token_urlsafe(32))'):admin:local-admin"
docker compose up --build
```

The API listens on `http://localhost:8000`, and data is stored in the `shelfsense-data` volume.

## Configuration

| Variable | Required | Description |
|---|---:|---|
| `API_KEYS` | Yes | Comma-separated `secret:role:subject` entries |
| `APP_ENV` | No | `development`, `test`, or `production` |
| `DATABASE_PATH` | No | SQLite path; defaults to `shelfsense.db` |
| `ALLOWED_ORIGINS` | No | Comma-separated browser origins |

Production rejects wildcard CORS origins and refuses to start without `API_KEYS`.

## Roles

| Capability | Viewer | Operator | Administrator |
|---|:---:|:---:|:---:|
| Read catalogue and stock | Yes | Yes | Yes |
| View reports and exports | Yes | Yes | Yes |
| Receive and issue stock | No | Yes | Yes |
| Create products | No | Yes | Yes |
| Create suppliers | No | No | Yes |
| Read audit events | No | No | Yes |

## API overview

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/healthz` | Process liveness |
| `GET` | `/readyz` | Database readiness |
| `POST` | `/api/v1/products` | Add a product |
| `GET` | `/api/v1/products` | List and filter products |
| `GET` | `/api/v1/products/{sku}` | Read a product |
| `POST` | `/api/v1/suppliers` | Add a supplier |
| `GET` | `/api/v1/suppliers` | List suppliers |
| `POST` | `/api/v1/inventory/receipts` | Receive stock |
| `POST` | `/api/v1/inventory/issues` | Issue stock |
| `GET` | `/api/v1/inventory/levels` | Read current stock |
| `GET` | `/api/v1/reports/inventory-summary` | Read inventory metrics |
| `GET` | `/api/v1/reports/inventory.csv` | Download inventory CSV |
| `GET` | `/api/v1/audit-events` | Read administrator audit feed |

Interactive schemas are available through `/docs` and `/openapi.json`.

## Quality checks

```bash
make check
```

This runs Ruff and Pytest. Pull requests additionally build the production Docker image.

## Project structure

```text
app/
  api.py                  inventory HTTP routes
  auth.py                 API-key authentication and roles
  audit.py                immutable audit events
  catalog.py              product domain rules
  persistent_inventory.py durable inventory service
  purchase_orders.py      purchase-order state machine
  reporting.py            inventory metrics and CSV export
  store.py                transactional SQLite repository
  suppliers.py            supplier domain rules
tests/                     unit and API tests
docs/architecture.md       design and extension guidance
```

## Operational boundaries

The first stable release targets one service instance and one SQLite data volume. Use encrypted transport at the reverse proxy, rotate API keys through the deployment environment, back up the data volume, and avoid placing secrets in committed files. PostgreSQL, distributed locks, user sessions, and multi-location inventory are future adapters rather than claims of this release.

## Contributing and security

See [CONTRIBUTING.md](CONTRIBUTING.md) for the change workflow and [SECURITY.md](SECURITY.md) for private vulnerability reporting guidance.

## License

MIT — see [LICENSE](LICENSE).
