# lx-data-models

[![PyPI](https://img.shields.io/pypi/v/lx-dtypes.svg)](https://pypi.org/project/lx-dtypes/)
[![Python](https://img.shields.io/pypi/pyversions/lx-dtypes.svg)](https://pypi.org/project/lx-dtypes/)
[![CI](https://github.com/wg-lux/lx-data-models/actions/workflows/ci.yml/badge.svg)](https://github.com/wg-lux/lx-data-models/actions/workflows/ci.yml)
[![Documentation](https://github.com/wg-lux/lx-data-models/actions/workflows/docs.yml/badge.svg)](https://github.com/wg-lux/lx-data-models/actions/workflows/docs.yml)
[![codecov](https://codecov.io/github/wg-lux/lx-data-models/graph/badge.svg?token=132HVE8KSF)](https://codecov.io/github/wg-lux/lx-data-models)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

`lx-dtypes` provides typed models for clinical research data. It checks data
against study rules and versioned medical terminology. Applications can collect
validation findings during data capture and validate records before storage or
exchange. The package also supports FHIR conversion and Django integration.

> [!IMPORTANT]
> This project is research software. It is not a medical device and must not be
> used as the sole basis for clinical decisions.

## Highlights

- Reusable models for terminology, patient records, reports, and host integration.
- Versioned YAML knowledge bases with deterministic loading.
- Report-template checks for structure, coverage, and captured data.
- FHIR clinical data and terminology conversion.
- Type, test, and documentation checks in CI.

The package is in **alpha**. We aim to keep public imports stable. Releases
before `1.0` may include documented breaking changes.

## Installation

`lx-dtypes` supports Python 3.12.

```bash
python -m pip install lx-dtypes
```

## Quick start

Validate a study setup without raising for invalid input:

```python
from lx_dtypes.models.contracts.study_setup import StudySetupDefinition
from lx_dtypes.validation import validate_contract

result = validate_contract(StudySetupDefinition, {"schema_version": "1.0"})
for issue in result.report.issues:
    print(issue.code, issue.path, issue.message)

# result.value contains the typed model only when the contract is valid.
```

For ledger data, `assess_examination(knowledge_base, payload,
template_name="...")` checks terminology provenance and applies the selected
template's study rules. Findings are advisory; the host decides when to require
correction. See the [cross-layer validation guide](docs/guides/cross-layer-validation.md)
for error codes, evaluation status, and strict persistence boundaries.

Load a knowledge-base module shipped with the package:

```python
from lx_dtypes import load_knowledge_base

knowledge_base = load_knowledge_base("report_template_examples")

print(knowledge_base.config.knowledge_base_identity)
print(sorted(knowledge_base.report_template))
```

Registry-backed deployments require an exact module version. The
[knowledge-base authoring guide](docs/guides/knowledge-base-authoring.md)
explains versioning and deployment.

Provision the packaged catalog before starting a registry-backed host:

```bash
export LX_DTYPES_KB_REGISTRY=/var/lib/my-host/terminology/registry.json
lx-dtypes-kb-registry bootstrap
```

The command exits nonzero if the registry is invalid or a packaged identity
cannot load. Hosts must treat that failure as a startup blocker.

## Documentation

Follow the [reader roadmap](docs/index.md#reader-roadmap) from the model overview
to a working example, then choose terminology, reporting, or application
integration. You can start with the topic that fits your work.

Build the documentation locally with:

```bash
python -m pip install -e ".[docs]"
make -C docs html
```

## Development

Questions, documentation fixes, synthetic examples, and code changes are useful
ways to contribute. Start with [CONTRIBUTING.md](CONTRIBUTING.md) for setup,
checks, and pull requests. See [CHANGELOG.md](CHANGELOG.md) for release notes
and [SECURITY.md](SECURITY.md) for vulnerability reporting.

For scoped repository navigation, start at [structure.yml](structure.yml) and
follow the [agent context guide](docs/agent_context.md).

## License and citation

Distributed under the [MIT License](LICENSE). If you use `lx-dtypes` in
published work, cite the project using [CITATION.cff](CITATION.cff).
