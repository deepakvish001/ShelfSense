# Contributing

## Development workflow

1. Create a focused branch from `main`.
2. Install development dependencies with `pip install -e '.[dev]'`.
3. Add or update tests with the behavior change.
4. Run `make check`.
5. Open a pull request describing behavior, validation, and operational impact.

Keep pull requests independently useful. Avoid mixing formatting, refactoring, and feature work unless they are inseparable.

## Commit style

Use short imperative messages such as `feat: add supplier lookup` or `fix: reject duplicate movement reference`.

## Database changes

Make schema initialization idempotent, preserve existing data, add indexes for new lookup patterns, and cover reopen or migration behavior with temporary-database tests.

## Security changes

Never commit API keys, database copies, personal data, or production environment files. Report vulnerabilities privately as described in `SECURITY.md`.
