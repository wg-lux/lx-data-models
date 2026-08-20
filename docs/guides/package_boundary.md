# Package Boundary Guide

`lx-data-models` should be treated as a package boundary when used from sibling
applications such as `endoreg-db`.

## Rules

- Import through public package modules when an `__init__.py` export exists.
- Do not import test modules, test fixtures, or example scripts from consuming
  applications.
- Keep generated demo artifacts under `temp/generated_exports/` or test-local
  `tmp_path` directories.
- Tests must not write tracked files into repository roots.
- Django ORM models are persistence adapters; cross-service payloads belong in
  Pydantic contracts and package-level interfaces.

## Generated Output Convention

- Example scripts may write to `temp/generated_exports/`.
- Tests should use `tmp_path` and assert on generated files there.
- Golden fixtures, if intentionally committed, should live under explicit test
  data directories rather than package roots.

## Test Layout

- Unit tests mirror the production package beneath `tests/unit/lx_dtypes/`.
- Python fixture providers and golden inputs live beneath `tests/fixtures/`.
- Repository-wide integration and package-boundary tests live directly beneath
  `tests/`.
- Test-only Django settings and pytest configuration belong to `tests/`, never
  to the distributable `lx_dtypes` package.
