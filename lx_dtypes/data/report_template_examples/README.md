# How To Write A Report Template

This is the fastest, easiest guide for creating a working report template.

If you only read one thing: all links are **exact string matches**.
`upper_gi` is different from `upper-gi` and different from `Upper_GI`.

## What A Report Template Actually Is

A report template is not the medical report itself.

It is a definition that says:

- which examination the template belongs to
- which sections should appear in the report
- which findings belong in those sections
- which extra rules should be checked when a real report is validated

Think of it as two layers combined:

1. Structure
   What the report is supposed to contain.
2. Validation rules
   What makes a filled report complete or incomplete.

In this repository, a report template is loaded from YAML into Pydantic models, stored in the `KnowledgeBase`, exported into resolved JSON for frontend/API use, and optionally evaluated against a real `PExamination` payload at runtime.

## The Five Pieces You Need To Know

When you read report-template YAML, separate these objects clearly:

- `report_finding`
  A reusable finding requirement. It says "this finding may appear here, and these classifications belong with it."
- `report_template_section`
  A named section inside the report template. It groups findings and controls ordering.
- `findings_validator`
  One concrete rule about a finding. Example: "if size is >= 10, `lst` must also be present."
- `examination_validator`
  A named bundle of validator references. It lets you compose multiple checks into one reusable group.
- `report_template`
  The top-level object tying everything together for one examination.

That means:

- sections define what the report looks like
- validators define how completion is judged
- the template chooses which sections and validators are used

## Before You Start

This file explains the current YAML format.

It does not mean the format is suitable for non-technical self-service authoring.

Current readiness:

- Good enough for engineers or technical product owners
- Good enough for clinician plus engineer collaboration
- Not good enough for unsupported editing by non-technical staff

The copy installed from the `lx-dtypes` wheel is immutable release content.
Runtime builder APIs must not edit files in `site-packages`. Import an editable,
versioned terminology bundle before saving a new template or changing lifecycle
state. Packaged templates are published by the protected package release
workflow and verified from the built wheel.

Why not:

- exact string matching is required everywhere
- validator operators must use specific canonical names
- dependencies and references are easy to break
- there is no form-based editor in this repository that prevents invalid combinations

Recommended workflow:

1. Non-technical/domain users write the intended report structure in plain language.
2. A technical owner translates that into YAML.
3. The technical owner runs validation.
4. The domain user reviews the resolved output and example validation results.

If you want a true non-technical workflow later, build a constrained editor on top of these models instead of asking users to edit YAML directly.

## Autoritative Konzeptabdeckung

Produktionsfähige Vorlagen benötigen zusätzlich eine explizite
`coverage_version` und `coverage_concepts`-Matrix. Diese Matrix ist keine
Beschreibung aus freiem Text: Jede anwendbare Regel benötigt eine stabile
Konzept-ID, einen Wertpfad oder Befund-Selector, eine autorisierte Wertemenge
und die zugehörigen Validatornamen.

Die Runtime liefert technische Coverage serverseitig. Eine Vorlage ohne diese
Metadaten wird absichtlich abgewiesen; das Frontend darf fehlende Coverage nur
als nicht autoritativen Fallback anzeigen. Die vollständige Authoring- und
Freigabereferenz steht in
[`docs/guides/report-concept-coverage.md`](../../../docs/guides/report-concept-coverage.md).

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
  section_kind: findings
  types:
    - baseline
  fields: []
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

Important distinction:

- `report_template_section.findings[]` decides which findings the template exposes
- `report_template.validators.*[]` decides which extra runtime checks the template executes

Those are related, but they are not the same thing.

## Naming Rules (Strongly Recommended)

- Use `snake_case` only.
- Use ASCII only.
- Do not mix separators (`_` and `-`) for ids.
- Keep names unique inside your module.

## Authoring Rule For Non-Technical Reviewers

If a non-technical reviewer needs to check a template, ask them to review only:

- the ordered list of sections
- the human meaning of findings and classifications
- the plain-language intent of each validator

Do not ask them to review:

- module wiring
- YAML syntax
- exact identifier spelling
- operator/comparator compatibility

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

## Section Kinds And Fields

`report_template_section` is no longer only a bucket of findings.

It can also describe non-finding sections:

- `section_kind: findings`
- `section_kind: patient_data`
- `section_kind: history`

Optional `fields` let you declare simple section fields such as patient-level or history-level keys:

```yaml
- model: report_template_section
  name: patient_context
  position: 1
  section_kind: patient_data
  fields:
    - key: age
      required: true
      source: patient
    - key: asa_score
      required: false
      source: history
  findings: []
```

Newcomer shortcut:

- use `findings` when the section is about reportable findings
- use `fields` when the section is about plain patient/history metadata

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

## What Validates What

This is the boundary that usually confuses new readers:

- YAML parsing validates shape:
  "is this record a valid `report_template`/`findings_validator`/etc. object?"
- `KnowledgeBase` loading validates wiring:
  "do these records load cleanly into the module, and are names unique?"
- structure/graph validation checks references and dependency layout:
  "does this template point at sensible sections and validators?"
- runtime validation checks a real report payload:
  "does this actual `PExamination` satisfy the template rules?"

So:

- a template can be syntactically valid YAML and still be a bad design
- a template can load successfully and still fail runtime checks for a real report
- `required: true` in template content means "expected by the template", not "already satisfied by some incoming report"

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

Plain-language meaning:

- "this finding may appear in the report"
- "these classifications belong to that finding"
- "required: true" means the report template expects it, not that an actual report already satisfies it

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

Plain-language meaning:

- "if this condition is true, then these classifications must also be present"

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

Plain-language shortcut:

- `findings_validator`: one concrete rule
- `examination_validator`: a named bundle of rules
- `report_template.validators`: which rules this template should actually use

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

## Release Checklist

Before using a template in production:

- [ ] The template loads successfully.
- [ ] Structure validation passes.
- [ ] Runtime validation was tested with at least one passing payload.
- [ ] Runtime validation was tested with at least one failing payload.
- [ ] A domain reviewer checked the resolved template output.
- [ ] A technical owner checked the YAML references and dependency module names.

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

## Historical Runtime Validation

If you validate a historical `PExamination` payload, you can now include:

- `knowledge_base_module`
- `knowledge_base_version`

Important:

- `knowledge_base_version` only works when deployment has provisioned that version through `LX_DTYPES_KB_REGISTRY`
- if the version is not available locally, runtime validation fails closed instead of silently using the current module version
- route `module_name` is still present in the API for compatibility, but payload KB identity is authoritative when supplied

## Mapping To `base_api` Requirement Objects

When using the new requirement endpoints in `lx_dtypes/django/api/main.py`, requirement objects are projected directly from report templates and validators.


Requirement projection inside each set:
- Validators are flattened in this order:
  1. `report_template.validators.findings_validators`
  2. `report_template.validators.examination_validators`
- `requirement.name` == validator name
- `requirement.kind` == `findings_validator` or `examination_validator`
- `requirement.id` == 1-based local index within that requirement set

Notes:
- These projected IDs are not persisted DB IDs.
- IDs can change when template names/order change.

## Next Read

For deeper internals, read:

- `docs/guides/report-template-infrastructure.md`
