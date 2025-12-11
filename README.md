# lx-data-models

[![PyPI](https://img.shields.io/pypi/v/lx-dtypes.svg)](https://pypi.org/project/lx-dtypes/)
[![CI](https://github.com/wg-lux/lx-data-models/actions/workflows/ci.yml/badge.svg)](https://github.com/wg-lux/lx-data-models/actions/workflows/ci.yml)
[![Docs](https://github.com/wg-lux/lx-data-models/actions/workflows/docs.yml/badge.svg)](https://github.com/wg-lux/lx-data-models/actions/workflows/docs.yml)
[![Publish](https://github.com/wg-lux/lx-data-models/actions/workflows/publish.yml/badge.svg)](https://github.com/wg-lux/lx-data-models/actions/workflows/publish.yml)

*CodeCov (Main)*
[![codecov](https://codecov.io/github/wg-lux/lx-data-models/graph/badge.svg?token=132HVE8KSF)](https://codecov.io/github/wg-lux/lx-data-models)
![Codecov icicle graph](https://codecov.io/github/wg-lux/lx-data-models/graphs/icicle.svg?token=132HVE8KSF)

*CodeCov (Dev)*
[![codecov](https://codecov.io/github/wg-lux/lx-data-models/branch/dev/graph/badge.svg?token=132HVE8KSF)](https://codecov.io/github/wg-lux/lx-data-models)
![Codecov icicle graph](https://codecov.io/github/wg-lux/lx-data-models/graphs/icicle.svg?token=132HVE8KSF)


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

## Contributing
See `CONTRIBUTING.md` for the full workflow, coding standards, and release
guidelines. Bug reports and pull requests are welcome!

## License
Distributed under the MIT License. See `LICENSE` for details.