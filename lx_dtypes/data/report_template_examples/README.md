# How To Write A Report Template

This is the fastest, easiest guide for creating a working report template.

If you only read one thing: all links are **exact string matches**.
`upper_gi` is different from `upper-gi` and different from `Upper_GI`.

## What You Edit

Create or update two files:

1. `config.yaml`
2. `report_templates.yaml`

## 1. Minimal `config.yaml`

```yaml
name: my_report_templates
version: 0.1.0
modules: []
depends_on:
  - sample_knowledge_base
data:
  files:
    - "./report_templates.yaml"
```

Rules:
- `name` is your module id. Use this later in API paths.
- `depends_on` should include modules your findings/classifications rely on.

## 2. Minimal `report_templates.yaml` (Copy/Paste Starter)

```yaml
- model: report_finding
  name: esophagus_polyp_finding
  finding: esophagus_polyp
  required: true
  multiple_allowed: false
  classifications: []

- model: report_template_section
  name: baseline_section
  position: 0
  types:
    - baseline
  findings:
    - esophagus_polyp_finding

- model: examination_validator
  name: baseline_validator
  finding_validators: []
  examination_validators: []

- model: report_template
  name: upper_gi_basic
  examination: star_upper_gi_endoscopy
  report_sections:
    - baseline_section
  validators:
    examination_validators:
      - baseline_validator
    findings_validators: []
```

## How References Work

These fields must reference existing names exactly:

- `report_template.report_sections[]` -> `report_template_section.name`
- `report_template_section.findings[]` (string form) -> `report_finding.name`
- `report_template.validators.examination_validators[]` -> `examination_validator.name`
- `report_template.validators.findings_validators[]` -> `findings_validator.name`
- `examination_validator.finding_validators[]` -> `findings_validator.name`
- `examination_validator.examination_validators[]` -> `examination_validator.name`

## Naming Rules (Strongly Recommended)

- Use `snake_case` only.
- Use ASCII only.
- Do not mix separators (`_` and `-`) for ids.
- Keep names unique inside your module.

## Inline vs Referenced Findings

Inside a section, findings can be:

- string reference: `- esophagus_polyp_finding`
- inline object:
  ```yaml
  - finding: esophagus_polyp
    required: true
    multiple_allowed: false
    classifications: []
  ```

Recommendation:
- For beginners, use **string references only** for consistency.
- If you mix styles, keep field names consistent.

## Validator Alias Note

`finding_validator` is accepted as an alias for `findings_validator`.

Recommendation:
- Always write `findings_validator` to avoid confusion.

## Findings Validator Operators And Comparators

Canonical operators:
- `exists`
- `missing`
- `conditional`

Canonical comparators:
- `eq`, `ne`
- `gt`, `gte`
- `lt`, `lte`
- `in`
- `not_in`

YAML rule:
- Use only the canonical values above in committed knowledge-base YAML.
- Deprecated aliases may still be accepted at direct model-parse time for backward compatibility, but they must not appear in persisted terminology or report-template files.

## Quick Validation Checklist

Before committing:

- [ ] Every referenced section name exists.
- [ ] Every referenced validator name exists.
- [ ] No duplicate `name` values in the module.
- [ ] No `snake_case` vs `kebab-case` drift.
- [ ] No circular `examination_validator` chains.

## Useful Checks

Run the audit script (from `lx-data-models` root):

```bash
python scripts/audit_fixture.py \
  --config lx_dtypes/data/my_report_templates/config.yaml \
  --data-root lx_dtypes/data
```

Test API output:

- `GET /base_api/report-templates/{module_name}/{template_name}`
- `GET /base_api/report-templates/by-examination/{module_name}/{examination_name}`

## Mapping To `base_api` Requirement Objects

When using the new requirement endpoints in `lx_dtypes/django/api/main.py`, requirement objects are projected directly from report templates and validators.

Requirement set projection:
- Endpoint: `GET /base_api/requirement-sets`
- One requirement set == one `report_template`
- `requirement_set.name` == `report_template.name`
- `requirement_set.type` == `report_template.examination`
- `requirement_set.id` == 1-based index over `sorted(report_template names)`

Requirement projection inside each set:
- Validators are flattened in this order:
  1. `report_template.validators.findings_validators`
  2. `report_template.validators.examination_validators`
- `requirement.name` == validator name
- `requirement.kind` == `findings_validator` or `examination_validator`
- `requirement.id` == 1-based local index within that requirement set

Evaluation projection:
- Endpoint: `POST /base_api/evaluate-requirement-set`
- Selected set ids resolve back to template names.
- Runtime call per template:
  - `kb.evaluate_report_template_validators(template_name, reported_findings=...)`
- Result row mapping:
  - `requirement_name` -> runtime validator `name`
  - `met` -> runtime validator `ok`
  - `details` -> summary message built from validator issues
  - `validator_result` -> full validator runtime object

Notes:
- These projected IDs are not persisted DB IDs.
- IDs can change when template names/order change.

## Next Read

For deeper internals, read:

- `docs/guides/report-template-infrastructure.md`
