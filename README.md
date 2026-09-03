# ShelfSense

Inventory intelligence for small retailers, pharmacies, and local warehouses.

ShelfSense tracks stock batches, expiry dates, reorder thresholds, suppliers, and inventory movements. The first release focuses on a clean REST API that can later support a web dashboard and barcode workflows.

## Core capabilities

- Product and category catalogue
- Batch-level stock and expiry tracking
- Low-stock and near-expiry alerts
- Supplier records and purchase intake
- Immutable inventory movement history
- Dashboard-ready summary endpoints

## Technology

- Python 3.12
- FastAPI and Pydantic
- SQLAlchemy with SQLite locally and PostgreSQL in production
- Pytest for automated tests
- Ruff for linting
- GitHub Actions for continuous integration

## Local setup

1. Create and activate a Python 3.12 virtual environment.
2. Install the package with `pip install -e '.[dev]'`.
3. Copy `.env.example` to `.env`.
4. Start the API with `uvicorn app.main:app --reload`.
5. Open `http://localhost:8000/docs`.

## Quality commands

```bash
ruff check .
pytest
```

## Project layout

```text
app/           API and inventory domain
tests/         automated tests
.github/       continuous integration
```

## License

MIT
