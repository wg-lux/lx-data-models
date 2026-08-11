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
Install the latest release from PyPI:

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

## FHIR And YAML

FHIR terminology can be converted directly into a validated knowledge base:

```python
from lx_dtypes.models.interface.KnowledgeBase import KnowledgeBase

kb = KnowledgeBase.from_fhir(
    fhir_bundle,
    module_name="imported_gastroenterology",
)
```

To generate a single YAML file that can be loaded again with
`KnowledgeBase.create_from_yaml`:

```python
from lx_dtypes.models.knowledge_base.fhir_yaml import write_fhir_yaml

path = write_fhir_yaml(
    fhir_bundle,
    "generated/imported_gastroenterology.yaml",
    module_name="imported_gastroenterology",
    language="en",
)
```

Use `fhir_to_yaml(...)` when YAML text is needed without writing a file, or
`knowledge_base_from_fhir(...)` for the equivalent standalone conversion API.
The high-level APIs use FHIR concept codes as stable internal identifiers and
retain displays and language designations in `name_en` and `name_de`. Repeated
conversion of the same input is deterministic.

Set `language` to the IETF language tag of the FHIR `concept.display` values
(for example `"en"`, `"de-DE"`, or `"pt-BR"`). For mixed-language bundles, set
`CodeSystem.language` on each resource instead; the explicit API argument takes
precedence. English and German displays are assigned to the corresponding LXDM
translation field. Other source languages remain available as the stable concept
code while explicit English or German FHIR designations are retained. Omitting
both language declarations preserves the legacy behavior of using an
undesignated display for both LXDM translation fields.

By default, high-level conversion rejects payloads without mappable terminology
`CodeSystem` resources and duplicate codes. Exact LX resource IDs take precedence;
unknown CodeSystems are conservatively mapped from their declared properties,
metadata, and concept text to the most likely LXDM domain. Resources without
positive structural or textual evidence remain unmapped. Pass `strict=False` to
allow an empty knowledge base. The currently supported domains are examination,
finding, classification type, classification, classification choice, and unit.
Nested FHIR concepts are imported recursively and flattened into the selected
LXDM collection because LXDM concept collections are keyed rather than hierarchical.

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

## Terminology Editor Publish Workflow

Terminology bundles published from `lx-terminology-editor` can be committed into
this package under `lx_dtypes/data/<sanitized_bundle_name>/`. The published
directory is a normal knowledge-base module: it contains a root `config.yaml`
and child module directories such as `lx_units`, `lx_findings`, and
`lx_classifications`.

Once the published directory exists in the package data root, consumers can load
it through the default resolver without passing explicit paths:

```python
from lx_dtypes.models.interface import load_knowledge_base

kb = load_knowledge_base("<sanitized_bundle_name>")
```

This unversioned convenience applies only when no registry is configured. With
`LX_DTYPES_KB_REGISTRY`, callers must pass the exact registered version and the
resolver does not fall back to packaged or checkout data.

The loader resolves child modules relative to the selected bundle first. This
allows an editor-published `lx_units` module to coexist with the canonical
`lx_dtypes/data/terminology/lx_units` module without being mixed into the wrong
bundle. For pinned deployments, register the same bundle directory with
`LX_DTYPES_KB_REGISTRY` and load it with an explicit `version`.

Top-level `demo-data/` is intentionally not part of the default Python package
data resolution path. Use it explicitly with `DataLoader(input_dirs=[...])` in
authoring or tests, or publish it as a versioned `LX_DTYPES_KB_REGISTRY` entry.
Normal unversioned loads use only the immutable `lx_dtypes/data` content shipped
in the installed package. Runtime checkout and `LOOKUP_DTYPES_DATA_ROOT`
overlays are not supported.

`lx-annotate` can also import the editor ZIP directly through
`POST /dtypes-api/terminology/bundles/import`. The endpoint extracts the ZIP into
`LX_DTYPES_TERMINOLOGY_IMPORT_ROOT` (or a `terminology-packages/` directory next
to the configured registry), validates it with the normal knowledge-base loader,
updates the registry, and activates the imported version.

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

1. Update `CHANGELOG.md` and bump the Python distribution version in
   `pyproject.toml`. Do not rewrite knowledge-base module versions as part of a
   Python package release.
2. Refresh and install the locked development toolchain with `uv lock` and
   `uv sync --locked --extra dev`. This currently provides the Twine version
   required to validate the build backend's package metadata.
3. Run formatting, linting, type-checking, and the full test suite.
4. Run `uv run --locked --extra dev lx-dtypes-release build`. The helper
   validates only the wheel and sdist for the current project version, even if
   `dist/` contains older artifacts. Never upload a reused `dist/*` glob.
5. Trigger the "Publish" GitHub workflow (either via tag/release or manual
	dispatch). Trusted Publisher entries for `test.pypi.org` and `pypi.org`
	should already reference the `publish.yml` workflow and the `testpypi`/`pypi`
	environments; approve those environments as needed and the workflow will
	push to TestPyPI first, then PyPI.

### Easier Release Commands

```bash
uv run --locked --extra dev lx-dtypes-release current
uv run --locked --extra dev lx-dtypes-release prepare 0.2.14
uv lock
uv run --locked --extra dev lx-dtypes-release build
git tag v0.2.14 && git push origin v0.2.14
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
