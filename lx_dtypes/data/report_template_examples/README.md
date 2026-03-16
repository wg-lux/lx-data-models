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
- `condition`

Canonical comparators:
- `eq`, `ne`
- `gt`, `gte`
- `lt`, `lte`
- `in`, `not_in`

Do not use legacy aliases such as:
- `present`
- `absent`
- `not_exists`
- `not-exists`
- `if`

Those aliases are no longer accepted in strict validation.

## Expand The Example Module With Validator-Ready Content

Use this pattern when you want a report template to project into requirement-like runtime checks.

### 1. Add a reusable `report_finding`

```yaml
- model: report_finding
  name: rf_esophagus_polyp
  finding: esophagus_polyp
  required: true
  multiple_allowed: false
  classifications:
    - classification: size_mm
      required: false
    - classification: lst
      required: false
```

This is frontend-facing template content. It tells the editor what finding can appear in the report, not whether the report is already complete.

### 2. Add a `findings_validator`

```yaml
- model: findings_validator
  name: polyp_has_lst_if_large
  level: error
  query:
    finding: esophagus_polyp
    operator: condition
    condition:
      all:
        - classification: size_mm
          comparator: gte
          value: 10
      then_requires:
        - classification: lst
```

Use `condition` when the requirement depends on a value or classification, not just presence.

Use `exists` for pure presence checks:

```yaml
- model: findings_validator
  name: report_has_esophagus_polyp
  level: error
  query:
    finding: esophagus_polyp
    operator: exists
```

Use `missing` for explicit absence checks:

```yaml
- model: findings_validator
  name: no_duplicate_large_polyp_marker
  level: warning
  query:
    finding: duplicate_large_polyp_marker
    operator: missing
```

### 3. Group findings validators under an `examination_validator`

```yaml
- model: examination_validator
  name: upper_gi_baseline_requirements
  finding_validators:
    - report_has_esophagus_polyp
    - polyp_has_lst_if_large
  examination_validators: []
```

This is how you create a reusable requirement group for one examination template.

### 4. Attach validators to the `report_template`

```yaml
- model: report_template
  name: upper_gi_basic
  examination: star_upper_gi_endoscopy
  report_sections:
    - baseline_section
  validators:
    examination_validators:
      - upper_gi_baseline_requirements
    findings_validators:
      - report_has_esophagus_polyp
      - polyp_has_lst_if_large
```

Practical rule:
- put reusable cross-finding logic into `examination_validators`
- put direct finding checks into `findings_validators`
- attach both at the template level if frontend/export and runtime evaluation should see them

## Validator-Ready Authoring Checklist

- [ ] Every `finding` in a validator exists in the module or dependencies.
- [ ] Every `classification` used in `condition` or `then_requires` exists for that finding.
- [ ] Operators are canonical only: `exists`, `missing`, `condition`.
- [ ] Comparators are canonical only: `eq`, `ne`, `gt`, `gte`, `lt`, `lte`, `in`, `not_in`.
- [ ] `report_template.validators.*` references existing validator names exactly.
- [ ] `examination_validator.finding_validators[]` references existing `findings_validator` names exactly.

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
