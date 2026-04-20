# lx-data-models

[![PyPI](https://img.shields.io/pypi/v/lx-dtypes.svg)](https://pypi.org/project/lx-dtypes/)
[![CI](https://github.com/wg-lux/lx-data-models/actions/workflows/ci.yml/badge.svg)](https://github.com/wg-lux/lx-data-models/actions/workflows/ci.yml)
[![Docs](https://github.com/wg-lux/lx-data-models/actions/workflows/docs.yml/badge.svg)](https://github.com/wg-lux/lx-data-models/actions/workflows/docs.yml)
[![Publish](https://github.com/wg-lux/lx-data-models/actions/workflows/publish.yml/badge.svg)](https://github.com/wg-lux/lx-data-models/actions/workflows/publish.yml)

*CodeCov (Main)*
[![codecov](https://codecov.io/github/wg-lux/lx-data-models/graph/badge.svg?token=132HVE8KSF)](https://codecov.io/github/wg-lux/lx-data-models)

*CodeCov (Dev)*
[![codecov](https://codecov.io/github/wg-lux/lx-data-models/branch/dev/graph/badge.svg?token=132HVE8KSF)](https://codecov.io/github/wg-lux/lx-data-models)

`lx-dtypes` provides strongly typed, Pydantic-powered data models for Lux Group
medical research projects. The package ships opinionated validators, utilities
for ingestion/export, and a common vocabulary so downstream services can reason
about patient examinations, knowledge-base entries, and related clinical data.

## Features
- Comprehensive Pydantic models covering patient records, exam findings, and
	knowledge-base entities.
- Data loaders/encoders that normalize multiple file formats into the same
	abstractions.
- Utilities for working with Lux Research tooling (paths, logging, export
	helpers, etc.).
- Ready-to-run pytest suite with coverage and optional type-checking.

## Installation
Install the latest release from PyPI (coming soon):

```bash
pip install lx-dtypes
```

For contributors and power users, install with the development extras:

```bash
pip install "lx-dtypes[dev]"
```

## Quick Start
```python
from lx_dtypes import __version__
from lx_dtypes.models.patient import Patient

patient = Patient.model_validate({
		"id": "1234",
		"first_name": "Ada",
		"last_name": "Lovelace",
})

print(patient.full_name)
print(__version__)
```

## Development

```bash
git clone https://github.com/wg-lux/lx-data-models
cd lx-data-models
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

## Architecture Notes

- Treat `lx-data-models` as a package boundary when consumed by sibling
  services.
- Import package-owned symbols through public modules where available.
- Keep demo outputs under `temp/generated_exports/`; tests should use `tmp_path`
  instead of writing repository-root artifacts.
- Do not import from `lx_dtypes...tests` or `...test_fixtures` in consuming
  applications.

## Django Integration

If you want to use the packaged Django API in another project, do not infer the
host-model requirements from the code. Use the explicit contract in
[docs/guides/django-host-integration.md](docs/guides/django-host-integration.md).

That guide defines:

- required settings such as `LX_DTYPES_HOST_MODELS_MODULE`
- the exact host ORM models that must be exported
- the required fields, relations, and methods on those models
- the supported URL mounting pattern

## Prototype KB Workflow

For fast local knowledge-base prototyping with `lx-terminology-editor`, keep the
editor's `.published/` output as the handoff artifact and point
`LX_DTYPES_KB_REGISTRY` at its registry JSON.

Inside `devenv shell`, this repo exposes:

- `LX_DTYPES_EDITOR_KB_REGISTRY`
- `use_editor_kb`
- `use_packaged_kb`
- `show_kb_mode`

Example:

```bash
use_editor_kb
lx-dtypes-prototype-kb-smoke --module my_module --version 0.1.0-dev.1
```

This keeps prototype loading deterministic because resolution happens through
the same versioned registry path used by `KnowledgeBaseResolver`.

## Migrations

The following command shortcuts are available for managing migratons, see line below for what they do:

mkmigrations
	
 "uv run python manage.py makemigrations ${DJANGO_APP_NAME}";

migrate

 "uv run python manage.py migrate";

runserver 

 "uv run python manage.py runserver";

resetdb

 "rm -f db.sqlite3";

resetmigrations

	rm -rf ${DJANGO_APP_DIR}/migrations/;
	uv run python manage.py makemigrations ${DJANGO_APP_NAME};


### Initialized Models
Some pydantic models with ForwardRefs require initialization before use.
Import initialized models from `lx_dtypes.utils.initialized_models`

If you encounter this error when using a model, you may add it there.

Example for the PatientLedger model which references Examiner. This would cause a circular import, therefore we just use the Examiner model during TYPE_CHECKING in the PatientLedger model file and rebuild the model here.
```python
from lx_dtypes.models.examiner import (
    Examiner,  # for model rebuild # type: ignore # noqa: F401
)

PatientLedger.model_rebuild()

```

### Test & Lint

```bash
pytest
ruff check lx_dtypes tests
mypy lx_dtypes
```

### Documentation
Install the documentation extras (included in `.[dev]`) and build the HTML site
with Sphinx:

```bash
pip install -e ".[docs]"
make -C docs html
# open docs/_build/html/index.html in your browser
```

Use `make -C docs linkcheck` to verify outbound references before publishing to
Read the Docs or GitHub Pages.



## Release Process
1. Update `CHANGELOG.md` and bump the version in `pyproject.toml`.
2. Run formatting, linting, type-checking, and the full test suite.
3. Build artifacts with `python -m build` and verify with `twine check dist/*`.
4. Trigger the "Publish" GitHub workflow (either via tag/release or manual
	dispatch). Trusted Publisher entries for `test.pypi.org` and `pypi.org`
	should already reference the `publish.yml` workflow and the `testpypi`/`pypi`
	environments; approve those environments as needed and the workflow will
	push to TestPyPI first, then PyPI.

### Easier Release Commands

```bash
lx-dtypes-release current
lx-dtypes-release prepare 0.1.2
lx-dtypes-release build
git tag v0.1.2 && git push origin v0.1.2
```

### Easier KB Registry Commands

Register the current installed knowledge base version and data root:

```bash
lx-dtypes-kb-registry add-current /path/to/kb_registry.json --module report_template_examples
```

Register an explicit historical version from a provisioned path:

```bash
lx-dtypes-kb-registry add /path/to/kb_registry.json \
  --module report_template_examples \
  --version 0.1.0 \
  --input-dir /nix/store/.../site-packages/lx_dtypes/data
```

Smoke-test an explicit prototype module/version through the configured registry:

```bash
lx-dtypes-prototype-kb-smoke --module report_template_examples --version 0.1.0
```

## Contributing
See `CONTRIBUTING.md` for the full workflow, coding standards, and release
guidelines. Bug reports and pull requests are welcome!

## License
Distributed under the MIT License. See `LICENSE` for details.
