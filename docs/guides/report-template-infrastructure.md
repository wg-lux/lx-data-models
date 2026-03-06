# Report Template Infrastructure

This guide explains exactly how the report-template YAML is loaded, validated, and exported to frontend JSON in this repository.

Start here for a beginner authoring guide:
- `lx_dtypes/data/report_template_examples/README.md`

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
- `findings_validator`
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
- `findings_validator`
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
- Runtime validator execution for `exists`, `missing`, and `conditional` operators via:
  - `KnowledgeBase.evaluate_report_template_validators(...)`
  - `POST /base_api/report-templates/{module_name}/{template_name}/validate`

Not implemented yet:

- Dedicated Django ORM models/migrations for report-template entities

## Runtime Validator Payload Shape

Use either:

- `KnowledgeBase.evaluate_report_template_validators(template_name, reported_findings=[...])`
- `POST /base_api/report-templates/{module_name}/{template_name}/validate`

Expected payload example:

```json
{
  "findings": [
    {
      "finding": "esophagus_polyp",
      "classifications": [
        {"classification": "size_mm", "value": 12},
        {"classification": "lst", "value": "present"}
      ]
    }
  ]
}
```

## Practical YAML Tips

1. Use ASCII identifiers for `name` and references (`esophagus_polyp` instead of `ösophagus_polyp`) to avoid cross-system key issues.
2. Keep references consistent:
   - section names used in `report_template.report_sections` must exist.
   - validator names used in `report_template.validators.*` should exist.
3. Use `finding_validator` or `findings_validator`; both parse, but canonical model is `findings_validator`.
