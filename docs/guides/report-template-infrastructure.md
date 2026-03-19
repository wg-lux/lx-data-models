# Report Template Infrastructure

This guide explains exactly how the report-template YAML is loaded, validated, and exported to frontend JSON in this repository.

Start here for a beginner authoring guide:
- `lx_dtypes/data/report_template_examples/README.md`

Use that README specifically for:

- adding `findings_validator` entries
- grouping them into `examination_validator` entries
- attaching validator-ready requirement content to `report_template.validators`

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

## Important Files

- Example module config: `lx_dtypes/data/report_template_examples/config.yaml`
- Example template YAML: `lx_dtypes/data/report_template_examples/report_templates.yaml`
- New model package: `lx_dtypes/models/knowledge_base/report_template/`
- Global KB model registry: `lx_dtypes/models/knowledge_base/main.py`
- YAML parser: `lx_dtypes/utils/parser.py`
- KB export methods: `lx_dtypes/models/interface/KnowledgeBase.py`
- Tests:
  - `lx_dtypes/models/interface/tests/test_report_template_example_module.py`
  - `lx_dtypes/models/interface/tests/test_report_template_export.py`

## Mental Model

Think of the flow as:

`YAML -> parse_shallow_object (A method, that will parse a yaml file into a pydantic structure) -> typed model -> KnowledgeBase dictionaries -> export_report_template -> frontend JSON`

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
  - `POST /base_api/report-templates/{module_name}/{template_name}/validate`
- Version-aware KB loading for runtime validation when a payload carries `knowledge_base_version`

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
- `POST /base_api/report-templates/{module_name}/{template_name}/validate`

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

Historical runtime note:

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
