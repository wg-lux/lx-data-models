# KB YAML Linting

Owner: lx-dtypes maintainers. This guide owns the `ok` authoring and CI checks.
Read the [package structure guide](dtypes-package-structure.md) before authoring YAML.

## Default quality gate

```bash
uv run ok
```

Without arguments, `ok` checks every current package under the installed
`data/terminology/` and `data/report_templates/` directories. It excludes retained
releases under `versions/`. Each package is checked with its own dependency closure;
independent packages are not merged into an artificial combined knowledge base.
The summary counts unique selected YAML files, not manifests or repeated dependencies.

Strict aliases, strict mixed finding styles, and failure on warnings are enabled
by default. Exit status `0` means no enabled check reported an error or warning;
status `1` means the quality gate failed. Diagnostics include source locations and
stable issue codes. Shared findings are printed once even when several packages
expose them. All selected packages are checked so one failure does not hide the rest.

## Check a specific package

```bash
uv run ok --config lx_dtypes/data/report_templates/coloreg/config.yaml
```

Repeat `--config` to check several independent packages. A positional `config.yaml`
works too. Passing a directory containing manifests checks those packages; explicitly
selected historical releases are checked without exemptions. Explicit selections
replace the default package list.

## What it checks

- YAML syntax, duplicate mapping keys (including manifests), and record structure.
- Duplicate `(model, name)` definitions within each dependency closure.
- Deprecated aliases and mixed finding-reference styles.
- Version markers embedded in record or package `name` values (`version_in_name`).
  Examples include `_v2`, `_version_2`, `@1.0.0`, `_1.2.3`, and `_1_0_0`.
  Store release versions in dedicated version fields. Size ranges, clinical stage
  identifiers and guideline years are not treated as release versions. Correcting
  a published identifier requires a coordinated migration, not an in-place rename.
- Authored German and English display names on clinical concepts and templates
  (`missing_language_coverage`). Sections may supply `title_de`/`title_en` or
  `name_de`/`name_en`. Missing, blank, non-string or placeholder values do not count;
  model-generated identifier fallbacks cannot conceal missing translations.
  Internal reporting references, validators and bibliographic identifiers do not
  require duplicate labels. Embedded host reference catalogues retain their own
  schema. This checks field coverage, not translation accuracy; descriptions have
  a single shared field and are not required in two languages.
- Missing descriptions for template findings, broken classification input chains,
  descriptor units, and descriptor-backed coverage paths.
- Runtime Pydantic model validation, dependency resolution, and definition conflicts.
- Canonical concept-graph validation, including dangling terminology references.
  Supported record kinds and aliases come from the runtime registry; dependency
  selection uses `DataLoader`, including semantic names that differ from folders.
  Ambiguous references and directory names used instead of declared module names
  are errors; no candidate is selected by filesystem order.
- Concepts defined locally in reporting/study packages, including inherited reporting
  packages; use terminology dependencies instead (`report_template_concept_definition`).
- Compilation and readiness of every loaded report template, including missing
  examinations, sections, findings and validators, empty sections/templates, and
  unsupported section fields. Issues that block publication are errors.

Draft status alone is not an error. Template readiness checks use the existing
reporting validator; `ok` does not publish templates or alter package data. A clean
result does not establish clinical correctness, host projection compatibility, or
validate separate study documents and host-owned sidecars.

## File-only checks and deliberate relaxation

```bash
uv run ok path/to/records.yml
```

Files or directories without manifests receive YAML lint and model-schema checks.
The output explicitly labels this limited scope: use `--config` to validate dependency
resolution and template readiness.

For exploratory work, `--no-fail-on-warnings` keeps warnings visible but allows exit
status `0` when there are no errors. `--no-strict-aliases` and
`--no-strict-mixed-styles` downgrade those specific errors to warnings. Existing
positive flags remain supported. Use the strict defaults for CI and publication.

The repository wrapper `python scripts/lint_kb_yaml.py` runs the same checks.
Keep pytest for runtime behavior and host integration tests.

See [knowledge-base authoring](knowledge-base-authoring.md) for publication workflows.
For creation, strict loading, and validation with ledger examples, use the
[`lx_dtypes.packages` workflow](dtypes-package-structure.md#create-load-and-validate-from-python).
It calls this same package checker and the existing ledger assessment API.
