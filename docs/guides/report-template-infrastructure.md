# Report Template Infrastructure

This guide explains how report-template YAML is loaded, validated, exported, and evaluated at runtime in this repository.

Start here for a beginner authoring guide:
- `lx_dtypes/data/report_template_examples/README.md`
This is the main system overview for report templates in this repository.

It explains how report-template YAML is:

- authored
- loaded into typed models
- validated structurally
- validated at runtime against report payloads
- exported to frontend JSON

Read the guides in this order:

1. Beginner authoring guide: `lx_dtypes/data/report_template_examples/README.md`
2. `docs/guides/django-host-integration.md`
3. This infrastructure guide
4. `docs/guides/report-template-graph-validation.md`
5. `docs/guides/report-template-findings-validator-migration.md`
6. `docs/guides/report-concept-coverage.md`

Use that README specifically for:

- adding `findings_validator` entries
- grouping them into `examination_validator` entries
- attaching validator-ready requirement content to `report_template.validators`

Use this guide when you want the full mental model rather than a copy-paste starter.

## Who This Is For

This guide is for:

- engineers implementing or integrating report-template behavior
- technical maintainers authoring YAML
- reviewers trying to understand where validation happens

It is not primarily a non-technical authoring guide.

## Vocabulary

These terms are easy to blur together. Keep them separate:

- `report_template`
  A frontend-facing template definition for one examination type.
- `report_template_section`
  A named section inside a template.
- `report_finding`
  A template-facing finding entry that can appear in a section.
- `findings_validator`
  A runtime rule about presence, absence, or conditional requirements for findings.
- `classification_validator`
  A runtime rule about classifications on a finding.
- `intervention_validator`
  A runtime rule about interventions on a finding.
- `unit_validator`
  A runtime rule about units attached to a classification.
- `examination_validator`
  A dependency/grouping validator that aggregates other validators.
- host Django integration contract
  The documented settings and ORM surface required to mount `lx_dtypes.django.api`
  in another Django project.
- structure validation
  Checks whether the template is wired correctly.
- graph validation
  Builds and checks a typed graph representation of template structure.
- runtime validation
  Evaluates an actual reported examination payload against template validators.
- concept coverage
  A versioned, server-generated evidence contract for the applicable concepts,
  values, validators, and payload paths of one report.

## Status Summary

Current state:

- Implemented:
  - typed YAML parsing
  - in-memory `KnowledgeBase` storage
  - resolved frontend JSON export
  - structural validation and graph validation
  - runtime validator execution
  - version-aware runtime KB loading through `KnowledgeBaseResolver`
  - API endpoints in `lx_dtypes/django/api/main.py` for export and validation
- Not implemented:
  - dedicated Django ORM persistence for report-template entities

Readiness for non-technical authors:

- Not ready for unsupported self-service editing.
- Ready for a guided workflow where a technical owner maintains the YAML and non-technical staff review the medical/reporting content.

Reason:

- authoring still requires exact string references, canonical operator names, dependency awareness, and validation tooling
- a small typo can break loading or silently change what gets linked
- there is no user-facing editor with guardrails in this repository

## Goal

You define report templates in YAML (sections, required findings, validators), and the backend:

1. parses YAML into typed Pydantic models,
2. stores them in `KnowledgeBase` (KB),
3. exports resolved JSON for frontend consumption.

## What A New Reader Should Understand First

A report template is not a filled medical report.

It is a knowledge-base definition that answers four questions:

1. Which examination is this template for?
2. Which sections should a report of that type contain?
3. Which findings or fields belong in those sections?
4. Which validation rules should be evaluated against a real report payload?

The important separation is:

- template structure:
  sections, findings, optional section fields
- runtime validation:
  validator objects evaluated against `PExamination`

If you mix those two ideas together, the codebase becomes hard to follow.

In short:

`YAML authoring -> typed KB models -> structure/graph validation -> runtime validation -> frontend export`

## Important Files

- Example module config: `lx_dtypes/data/report_template_examples/config.yaml`
- Example template YAML: `lx_dtypes/data/report_template_examples/report_templates.yaml`
- New model package: `lx_dtypes/models/knowledge_base/report_template/`
- Global KB model registry: `lx_dtypes/models/knowledge_base/main.py`
- YAML parser: `lx_dtypes/utils/parser.py`
- KB export methods: `lx_dtypes/models/interface/KnowledgeBase.py`
- Tests:
  - `tests/unit/lx_dtypes/models/interface/test_report_template_example_module.py`
  - `tests/unit/lx_dtypes/models/interface/test_report_template_export.py`

`report_template_examples` is package-owned example and test data. It is not a
clinical fallback module and it is not a valid builder write target. Production
resolution must use an explicitly provisioned registry identity.

## Versioned API And Builder Contract

Every report-template read, preview, validation, publication, and unpublication
request requires an exact knowledge-base version. GET and lifecycle routes use
the required `version` query parameter. Runtime validation additionally requires
the same version in the typed `PExamination` payload. A mismatch returns `409`
before template evaluation.

Builder save requests require both `module_name` and `module_version`. The
backend resolves that exact registry entry, verifies the loaded artifact
identity, and rejects package-owned sources. Blank modules never normalize to
`report_template_examples`.

Versioned resolver calls require either `LX_DTYPES_KB_REGISTRY` or explicit
`input_dirs`. They never fall back to installed package data roots. Unversioned
library loading remains available for explicit local authoring and test code,
but is not used by the versioned Django reporting contract.

## Mental Model

Think of the flow as:

`YAML -> parse_shallow_object (A method, that will parse a yaml file into a pydantic structure) -> typed model -> KnowledgeBase dictionaries -> export_report_template -> frontend JSON`

For runtime validation, add one more stage:

`frontend/API payload -> PExamination -> evaluate_report_template_validators(...) -> runtime result`
`YAML -> parse_shallow_object(...) -> typed model -> KnowledgeBase dictionaries -> export_report_template(...) -> frontend JSON`

The most important distinction is:

- authoring and structure validation happen on template definitions
- runtime validation happens on an actual patient examination payload

The runtime does not evaluate raw YAML directly. It evaluates already-parsed typed models.

## YAML Model Types

The new YAML `model` values are:

- `report_template`
- `report_template_section`
- `report_finding`
- `classification_validator`
- `findings_validator`
- `intervention_validator`
- `unit_validator`
- `examination_validator`

Alias supported:

- `finding_validator` is accepted and mapped to `findings_validator` in `lx_dtypes/utils/parser.py`.

## Current Contract Deltas

If you are working from an older report-template summary, these are the important updates:

- `report_template.validators` now includes:
  - `examination_validators`
  - `classification_validators`
  - `intervention_validators`
  - `unit_validators`
  - `findings_validators`
- `report_template_section` now also supports:
  - `section_kind`
  - `fields`
- `findings_validator` is stricter:
  - operators are canonical-only
  - `query.finding` / `query.operator` must align with the top-level `finding` / `operator`
  - `condition` rules have explicit structure and requirement references
- duplicate record names inside one module are now a hard load error with file and line information

## How Loading Works

1. `DataLoader.load_module_configs()` discovers module `config.yaml` files.
2. `DataLoader.load_knowledge_base(module_name)` builds the `KnowledgeBase`.
3. `KnowledgeBase.create_from_config(...)` iterates YAML files in `data.files`/`data.dirs`.
4. `parse_shallow_object(...)` reads each YAML item:
   - uses `model` to choose a target class from `knowledge_base_models_lookup`,
   - injects `kb_module_name` and `source_file`,
   - validates with Pydantic (`TargetModel.model_validate(...)`).
5. Parsed objects are stored in `KnowledgeBase` dict fields, keyed by `name`.

## How Frontend Export Works

Use:

- `KnowledgeBase.export_report_template(template_name)`
- `KnowledgeBase.export_report_templates()`

`export_report_template(...)` resolves references:

1. `report_template.report_sections` names -> actual `report_template_section` objects.
2. section `findings` entries:
   - if entry is inline object, keep it,
   - if entry is a string and matches `report_finding` name, expand it from `report_finding`.
3. validator names:
   - `validators.examination_validators` names -> expanded validator dicts when found,
   - `validators.findings_validators` names -> expanded validator dicts when found.

This gives frontend-ready JSON with section and validator detail materialized.

Important current behavior:

- missing `report_template_section` references are a hard failure during export
- missing validator references are soft and remain as strings in the export
- exported sections currently materialize:
  - `name`
  - `position`
  - `types`
  - resolved `findings`
- `section_kind` and `fields` exist in the typed model, but are not currently included in `export_report_template(...)`

## What Is Stored in KnowledgeBase

`KnowledgeBase` now has these new dict fields:

- `report_template_section`
- `report_finding`
- `classification_validator`
- `findings_validator`
- `intervention_validator`
- `unit_validator`
- `examination_validator`
- `report_template`

Their ddict/list exports are included in `KnowledgeBase.export_record_lists()`.

## Example Usage

```python
from pathlib import Path
from lx_dtypes.models.interface.DataLoader import DataLoader

loader = DataLoader(input_dirs=[Path("./lx_dtypes/data/")])
loader.load_module_configs()
kb = loader.load_knowledge_base("report_template_examples")

frontend_json = kb.export_report_template("star_upper_gi_main")
```

## Roundtrip Test Coverage

`test_report_template_example_module.py` verifies:

1. YAML module loads via `DataLoader`.
2. `export_report_template("star_upper_gi_main")` returns expected structure.
3. Export output survives JSON roundtrip (`json.dumps` -> `json.loads`).
4. `ReportTemplate` survives model JSON roundtrip (`model_dump_json` / `model_validate_json`).

## Current Scope and Non-Goals

Current scope:

- Typed YAML parsing
- In-memory `KnowledgeBase` storage
- Frontend JSON export
- Structural validation via `validate_report_template_structure(...)`
- Runtime validator execution for `exists`, `missing`, and `condition` operators via:
  - `KnowledgeBase.evaluate_report_template_validators(...)`
  - `POST /base_api/report-templates/{module_name}/{template_name}/validate?version={module_version}`
- Exact-version KB loading for runtime validation; the query and payload identities must match

Operators are strict canonical-only now:

- `exists`
- `missing`
- `condition`

Comparator set used by validator-ready content:

- `eq`, `ne`
- `gt`, `gte`
- `lt`, `lte`
- `in`, `not_in`

For migration details from legacy operator aliases, see:
- `docs/guides/report-template-findings-validator-migration.md`

Not implemented yet:

- Dedicated Django ORM models/migrations for report-template entities

## Validation Surface

There are two different kinds of validation:

1. Structure validation
   - checks that referenced sections exist
   - checks graph shape and template wiring
   - useful before runtime data is involved
2. Runtime validation
   - checks whether reported findings satisfy the validators attached to a template
   - useful when evaluating an actual report payload

For non-technical stakeholders, this distinction matters:

- structure validation answers "is this template wired correctly?"
- runtime validation answers "does this report satisfy the template rules?"

There is also a lower-level parse/load boundary before those:

- parser/model validation answers "does this YAML item match the expected Pydantic model?"
- `KnowledgeBase` loading answers "can these validated objects be assembled into one KB without duplicate names?"

For why runtime execution payloads are not modeled as canonical `ddict` objects
with `uuid`, see:

- `docs/guides/runtime-output-vs-canonical-ddict.md`

Graph validation is a third, narrower layer:

3. Graph validation
   - builds a typed graph from the already-loaded report-template structure
   - checks graph-oriented structure issues
   - supports downstream scoring/recommendation use cases

Use:

- structure validation when you are authoring or reviewing template wiring
- graph validation when you need graph-shaped downstream data or graph-specific checks
- runtime validation when you have an actual examination payload to evaluate

## Recommended Operating Model

For the current repository state, use this split:

1. Domain experts define the reporting intent
   - sections
   - required findings
   - plain-language rule intent
2. A technical owner translates that into YAML
   - references
   - validator operators/comparators
   - dependency/module wiring
3. Validation is run before rollout
   - structure validation
   - runtime validation with representative payloads
4. Domain experts review the generated/exported output
   - resolved template JSON
   - example validation results

Do not treat the raw YAML format as a safe end-user authoring surface yet.

## Runtime Validator Payload Shape

Use either:

- `KnowledgeBase.evaluate_report_template_validators(template_name, p_examination=...)`
- `POST /base_api/report-templates/{module_name}/{template_name}/validate?version={module_version}`

Expected typed examination payload example:

```json
{
  "patient": "test_patient",
  "knowledge_base_module": "report_template_examples",
  "knowledge_base_version": "0.1.0",
  "examination": "gastroscopy",
  "patient_findings": [
    {
      "finding": "esophagus_polyp",
      "patient_examination": "test_exam",
      "patient_finding_classifications": [
        {
          "patient_finding": "test_finding",
          "patient_finding_classification_choices": [
            {
              "classification": "size_mm",
              "classification_choice": "12",
              "patient_finding_classifications": "test_classifications",
              "patient_finding_classification_choice_descriptors": []
            }
          ]
        }
      ],
      "patient_finding_interventions": []
    }
  ]
}
```

## Runtime Validator Semantics

Runtime validation is executed in `ValidatorRuntime.py`. The runtime does not inspect raw YAML directly. It evaluates already-parsed typed models and first normalizes the incoming reported findings payload into this effective shape per finding occurrence:

- `finding`: normalized finding name
- `classifications`: `dict[str, list[Any]]`
- `classification_units`: `dict[str, list[str]]`
- `interventions`: `list[str]`

Normalization matters because the validators operate on this normalized structure, not on the original JSON field layout.

The runtime/model whitelist for validator comparison values is explicit:

- scalar values allowed in comparisons: `str | int | float | bool`
- list values allowed in params or multi-value payloads: `list[str] | list[int] | list[float] | list[bool]`

The validator model layer no longer uses open-ended `Any` for condition values or params.

### What each validator validates

`findings_validator`

- Target fields: `finding`, `operator`
- `exists`: passes if at least one occurrence of the target finding is present
- `missing`: passes if no occurrence of the target finding is present
- `condition`: for each occurrence of the target finding, evaluates the condition against that occurrence's classifications
- If the condition matches, `then_requires` is enforced
- `then_requires` can require:
  - classifications on the same finding occurrence
  - classification choices on the same finding occurrence
  - other findings anywhere in the normalized report
  - interventions on the same finding occurrence
  - units attached to a named classification on the same occurrence
  - one of several classification choices when a `classification_choice` requirement includes a `names` list

`classification_validator`

- Target fields: `finding`, `classification`, `operator`, `precedence`
- `exists`: passes if any occurrence of the target finding contains the target classification
- `missing`: passes if all occurrences of the target finding do not contain the target classification
- `condition`: for each occurrence of the target finding, evaluates the condition against that occurrence's classifications
- If the condition matches, the target classification must be present and any `then_requires` references must also be satisfied
- Returns a `hint` block derived from KB metadata, for example whether the classification appears binary, ordered, or non-categorical

`intervention_validator`

- Target fields: `finding`, `intervention`, `operator`, `precedence`
- `exists`: passes if any occurrence of the target finding contains the target intervention
- `missing`: passes if all occurrences of the target finding do not contain the target intervention
- `condition`: for each occurrence of the target finding, evaluates the condition against that occurrence's classifications
- If the condition matches, the target intervention must be present and any `then_requires` references must also be satisfied

`unit_validator`

- Target fields: `finding`, `classification`, `unit`, `operator`, `precedence`
- `exists`: passes if any occurrence of the target finding contains the target unit under the target classification
- `missing`: passes if all occurrences of the target finding do not contain that unit under that classification
- `condition`: for each occurrence of the target finding, evaluates the condition against that occurrence's classifications
- If the condition matches, the target unit must be present and any `then_requires` references must also be satisfied

`examination_validator`

- Does not inspect finding payload values directly
- It is a dependency validator that aggregates:
  - `finding_validators`
  - `examination_validators`
- It passes only if all referenced dependencies pass
- It also detects circular `examination_validator` references and returns an explicit runtime issue for that case

### Is validation purely string-based?

No. Identifier matching is mostly string-based, but value comparison is not purely string-based.

String-based parts:

- finding names
- classification names
- intervention names
- unit names
- validator names and dependency references

Value-aware parts:

- condition clause comparisons for classification values
- unit presence checks
- intervention presence checks

The runtime normalizes identifiers with permissive extraction rules. For mappings, it tries keys such as `name`, `key`, `slug`, `id`, `pk`, and `value` when turning something into an identifier.

For classification payload values, the runtime accepts multiple shapes and extracts a value from the first matching key:

- `value`
- `classification_choice`
- `classificationChoice`
- `choice`
- `values` for list-style payloads

This means identifier matching is string-oriented, but condition evaluation operates on actual extracted values.

### How numbers are handled

Number handling is implemented by `_coerce_numeric`, `_value_equals`, and `_compare_ordered`.

Rules:

- `int` and `float` values are treated as numeric
- numeric strings such as `"12"` or `"12.5"` are coerced to numbers
- booleans are explicitly not treated as numbers
- empty strings do not coerce to numbers

Comparator behavior:

- `eq` and `ne`
  - first try numeric equality if both sides can be coerced to numbers
  - otherwise compare via string form
- `gt`, `gte`, `lt`, `lte`
  - use numeric comparison if both sides can be coerced to numbers
  - otherwise fall back to lexical string comparison
- `in`, `not_in`
  - compare each candidate using the same equality logic as `eq`

Practical consequences:

- `"12"` and `12` compare equal
- `"12.0"` and `12` compare equal
- `"abc"` and `10` are compared as strings if a numeric comparator reaches them
- `True` is not treated as `1`

### Condition evaluation model

Conditions are evaluated against one finding occurrence at a time.

- `any`: at least one clause must match if the list is populated
- `all`: every clause must match if the list is populated
- both can be present; the occurrence must satisfy both branches

Each clause reads values from the normalized `classifications[classification_name]` bucket for that occurrence.

For `condition` validators:

- `triggered_occurrences` counts how many finding occurrences matched the condition
- validation only fails for those triggered occurrences
- non-triggering occurrences are ignored for the conditional requirement itself

### What is returned

Top-level template validation returns a `ReportTemplateRuntimeValidationResultDataDict` with:

- `template_name`
- `ok`
- `evaluated_findings_count`
- `classification_validators`
- `intervention_validators`
- `findings_validators`
- `examination_validators`
- `unit_validators`
- `issues`

`ok` is the conjunction of all validator result `ok` values. `issues` is the flattened union of every child validator issue list.

Per-validator result shapes:

`findings_validator` result:

- `name`
- `ok`
- `operator`
- `finding`
- `matched_occurrences`
- `triggered_occurrences`
- `missing_required_classifications`
- `issues`

`classification_validator` result:

- `name`
- `ok`
- `operator`
- `finding`
- `classification`
- `precedence`
- `matched_occurrences`
- `triggered_occurrences`
- `hint`
- `issues`

`intervention_validator` result:

- `name`
- `ok`
- `operator`
- `finding`
- `intervention`
- `precedence`
- `matched_occurrences`
- `triggered_occurrences`
- `hint`
- `issues`

`unit_validator` result:

- `name`
- `ok`
- `operator`
- `finding`
- `classification`
- `unit`
- `precedence`
- `matched_occurrences`
- `triggered_occurrences`
- `hint`
- `issues`

`examination_validator` result:

- `name`
- `ok`
- `finding_validator_status`
- `examination_validator_status`
- `issues`

Each issue object contains:

- `code`
- `level`
- `message`
- `validator_name`
- `validator_kind`
- optional `details`

### Failure modes documented by the runtime

The runtime returns explicit issues for several classes of failures:

- required finding, classification, intervention, or unit missing
- something present that should be missing
- unknown referenced validator name
- invalid conditional validator definition
- failed dependency in an `examination_validator`
- circular `examination_validator` dependency

This is why callers should inspect both:

- top-level `ok` for pass/fail
- `issues` and the per-validator arrays for actionable detail

Version-aware runtime loading is separate from template authoring:

- `knowledge_base_module` and `knowledge_base_version` are optional for current-version validation
- when `knowledge_base_version` is provided, the runtime must resolve that historical KB version through `LX_DTYPES_KB_REGISTRY`
- if the requested version is not provisioned locally, the runtime fails closed instead of silently using the current module version

Expected registry shape:

```json
{
  "modules": {
    "report_template_examples": {
      "0.1.0": "/nix/store/.../lx_dtypes/data"
    }
  }
}
```

## Practical YAML Tips

1. Use ASCII identifiers for `name` and references (`esophagus_polyp` instead of `ösophagus_polyp`) to avoid cross-system key issues.
2. Keep references consistent:
   - section names used in `report_template.report_sections` must exist.
   - validator names used in `report_template.validators.*` should exist.
3. Use `finding_validator` or `findings_validator`; both parse, but canonical model is `findings_validator`.
4. If you want the template to participate in requirement-style runtime evaluation, define:
   - `findings_validator` records for atomic checks
   - `examination_validator` records for grouping and recursion
   - `report_template.validators` references that attach those validators to the template

## Related Guides

- Beginner authoring: `lx_dtypes/data/report_template_examples/README.md`
- Graph-specific validation: `docs/guides/report-template-graph-validation.md`
- Operator migration for persisted validator data: `docs/guides/report-template-findings-validator-migration.md`
- Intentionally broken audit fixture: `docs/guides/fixtures/report-template-chaos/README.md`
