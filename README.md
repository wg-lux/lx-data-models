# lx-data-models

[![PyPI](https://img.shields.io/pypi/v/lx-dtypes.svg)](https://pypi.org/project/lx-dtypes/)
[![Python](https://img.shields.io/pypi/pyversions/lx-dtypes.svg)](https://pypi.org/project/lx-dtypes/)
[![CI](https://github.com/wg-lux/lx-data-models/actions/workflows/ci.yml/badge.svg)](https://github.com/wg-lux/lx-data-models/actions/workflows/ci.yml)
[![Documentation](https://github.com/wg-lux/lx-data-models/actions/workflows/docs.yml/badge.svg)](https://github.com/wg-lux/lx-data-models/actions/workflows/docs.yml)
[![codecov](https://codecov.io/github/wg-lux/lx-data-models/graph/badge.svg?token=132HVE8KSF)](https://codecov.io/github/wg-lux/lx-data-models)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

`lx-dtypes` is the reusable data-model package for Lux Group medical research
projects. It provides typed Pydantic contracts, versioned clinical terminology,
report-template validation, FHIR interoperability, and optional Django host
integration.

> [!IMPORTANT]
> This project is research software. It is not a medical device and must not be
> used as the sole basis for clinical decisions.

## Highlights

- Strict, reusable contracts for knowledge-base, ledger, reporting, and host
  integration boundaries.
- Version-aware YAML knowledge bases and deterministic loaders.
- Report-template graph, structure, coverage, and runtime validation.
- FHIR clinical and terminology conversion contracts.
- Typed package data with Pyright, pytest, and documentation checks in CI.

The package is currently in **alpha**. Public imports are kept stable where
possible, but releases before `1.0` may contain documented breaking changes.

## Installation

`lx-dtypes` supports Python 3.12.

```bash
python -m pip install lx-dtypes
```

## Quick start

Load a knowledge-base module shipped with the package:

```python
from lx_dtypes import load_knowledge_base

knowledge_base = load_knowledge_base("report_template_examples")

print(knowledge_base.config.knowledge_base_identity)
print(sorted(knowledge_base.report_template))
```

Registry-backed deployments should supply the exact module version. See the
[knowledge-base authoring guide](docs/guides/knowledge-base-authoring.md) and
[graph API guide](docs/guides/knowledge-base-graph-api.md) for the complete
workflow.

## Documentation

Start with the [documentation index](docs/index.md). Key guides include:

- [Package boundaries](docs/guides/package_boundary.md)
- [Data-model concept map](docs/guides/data-model-concept-map.md)
- [Knowledge-base authoring](docs/guides/knowledge-base-authoring.md)
- [Report-template infrastructure](docs/guides/report-template-infrastructure.md)
- [FHIR to LXDM mapping](docs/guides/fhir-lxdm-mapping-diagrams.md)
- [Django host integration](docs/guides/django-host-integration.md)

Build the documentation locally with:

```bash
python -m pip install -e ".[docs]"
make -C docs html
```

## Development

```bash
git clone https://github.com/wg-lux/lx-data-models.git
cd lx-data-models
uv sync --extra dev
uv run pyright
uv run pytest -q
uv run make -C docs html
```

Knowledge-base fixtures and tests must not contain patient data, credentials,
or machine-local paths. Generated output belongs in `temp/generated_exports/`
or a test-local temporary directory.

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full contributor and release
workflow, [CHANGELOG.md](CHANGELOG.md) for release notes, and
[SECURITY.md](SECURITY.md) for responsible vulnerability reporting.

## License and citation

Distributed under the [MIT License](LICENSE). If you use `lx-dtypes` in
published work, cite the project using [CITATION.cff](CITATION.cff).
