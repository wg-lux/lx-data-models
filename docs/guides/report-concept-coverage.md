# Authoritative Finding and Concept Coverage

Owner: lx_dtypes maintainers. This guide describes the versioned coverage
contract for clinical report templates. It is the technical reference for
template authors, backend and frontend developers, and clinical sign-off.

## Purpose and limits

For every approved reporting concept, coverage answers:

- Does the concept apply to the current examination?
- Is a value documented?
- Is the value valid according to the authorized value set?
- Which validators and payload paths support the result?

Coverage does not replace:

- clinical completeness,
- guideline adherence,
- clinical correctness of the concept matrix,
- an effectiveness or quality study.

Those statements need a separate, clinically annotated reference set and a
documented clinical sign-off.

## Authoritative data source

The authoritative result is computed on the server only, from:

1. the knowledge base that was actually loaded,
2. the identified report template,
3. the typed `PExamination` payload,
4. the runtime validators that were executed.

The validation routes return the result under `concept_coverage`:

```text
POST /report-templates/{module}/{template}/validate?version={module_version}
POST /report-templates/{module}/{template}/validate-from-ledger/{id}?version={module_version}
```

See the [HTTP API reference](../api/http.rst) for both routes. Frontends show
the server response. A local heuristic may only be used as a visibly labelled,
non-authoritative fallback for older responses.

## Identity and provenance

Every coverage result contains:

- `contract_version` (`report_concept_coverage_v1`),
- the module name, module version, and module digest,
- the template name, template version, and template digest,
- the resolver name and resolver version,
- a digest of the payload and the validator results.

An identity or digest mismatch must never be repaired automatically. The
operation must fail visibly and must not claim a clinically valid result.

## Concept metadata in a template

Every guideline-based template also publishes its versioned clinical
provenance under `guideline_references`. A reference contains a stable
guideline ID, the issuing organization, version, publication date, canonical
HTTPS address, and the statements, tables, or chapters actually used. A comment
in the YAML is not sufficient provenance, because consumers cannot check it.

```yaml
guideline_references:
  - guideline_id: AWMF-021-022
    title: S2k-Leitlinie Qualitätsanforderungen in der gastrointestinalen Endoskopie
    issuing_organization: DGVS
    version: "2.1"
    publication_date: 2025-07-01
    canonical_url: https://www.dgvs.de/.../S2k-LL-Qualitaetsanforderungen-Endoskopie-v2.1.pdf
    cited_sections:
      - Statement 2.36
      - Chapter 6.1 Colonoscopy
```

The `title` is the official title of the German guideline and stays in its
original language.

An applicable coverage concept needs at least:

```yaml
coverage_version: report_concept_coverage_v1
coverage_concepts:
  - concept_id: colon.polyp.size_mm
    label: Polyp size
    applicability_status: required
    validator_names:
      - colonoscopy_polyp_size_valid
    evidence_path:
      - patient_findings
    finding_selector:
      finding_name: colon_polyp
    concept_value_path:
      - patient_finding_classifications
      - "0"
      - patient_finding_classification_choices
      - "0"
      - classification_choice
    allowed_values:
      - "10"
      - "12"
    guideline_citations:
      - "AWMF-021-022 chapter 6.1.4: polyp classification"
```

The clinical template must define the actual value semantics. Example values
must not be adopted as a clinical value set without review.
`guideline_citations` is copied into the runtime coverage item, so consumers
can show the source directly next to the concept.

Open identifiers that cannot be enumerated must not be modelled as an
artificial `allowed_values` list. Use the closed checks
`value_constraint: non_empty_string` and
`value_constraint: non_empty_string_list` instead. They strictly check the type
and that the value is not empty; an `allowed_values` list must then not be
given as well. Numeric descriptor values use `value_constraint: number_range`
together with `numeric_min` and `numeric_max`; boolean and non-finite values
are explicitly rejected.

Use a `finding_selector` for repeated findings. The builder checks every
matching instance in stable payload order and returns the concrete
`evidence_paths`. A valid first match must not hide a later invalid one.

A `classification_choice` may only be given together with a
`classification_name`. A `not_applicable` concept needs no value path, but it
must have a clinically justified `applicability_reason`.

## Status semantics

Each coverage item has an applicability status, set by the template, and a
validation status, computed at runtime.

| Validation status | Meaning |
| --- | --- |
| `present` | A value is present, explicitly allowed, and all associated validators succeeded. |
| `missing` | No matching finding or instance was found. |
| `unknown` | The value or its context cannot be resolved, or a referenced validator returned no result. No positive statement is allowed. |
| `invalid` | A value is present but not allowed, or a validator failed. |
| `undetermined` | The concept is `not_applicable` under an approved rule, so it is not evaluated. |

`present` must never be derived from a lexical finding name alone or from the
mere existence of a JSON path. Missing units or unresolved synonyms must not
silently count as valid.

## Units: current limitation

The current `PExamination` and `PFinding` persistence models do not yet carry a
separate, reliable unit for patient finding values. A template must therefore
not report a unit as satisfied when the unit comes only from knowledge-base
metadata.

Unit safety needs its own versioned contract for value, unit, conversion, and
permitted tolerance. Until then, such concepts stay `unknown` or block
approval.

## Fail-closed rules

The runtime rejects a template with `422` when, among other things:

- `coverage_version` is missing or not supported,
- `coverage_concepts` is missing or empty, or stable concept IDs are missing,
- an applicable rule has no value path or selector,
- there are neither allowed values nor a matching typed value check,
- the validator response is malformed or lists a validator twice,
- the template identity does not match the route.

This is intentional. A template without a clinically authorized coverage matrix
is not ready for production and must not return a seemingly complete result.

A referenced validator that returns no result does not reject the template;
the affected concept is reported as `unknown`.

## Review and approval

Before clinical approval, at least the following are required:

1. Clinically annotated positive, negative, not-applicable, and invalid cases.
2. Tests for missing, unknown, and unresolved values.
3. Tests for several instances of the same finding type.
4. Evidence of the module and template version and digest.
5. Reproducible evidence paths and validator results.
6. Separate review of technical coverage and clinical completeness.
7. Documented clinical approval of value sets, rules, and units.

## Implementation

In this repository:

- Contract: `lx_dtypes/models/knowledge_base/report_template/ReportConceptCoverage.py`
- Template metadata: `ReportTemplateCoverage.py`
- Runtime builder: `ReportConceptCoverageBuilder.py`
- API: `lx_dtypes/django/api/report_template_routes.py`

In lx-annotate:

- Frontend contract: `frontend/src/types/reportTemplate.ts`
- Frontend display: `frontend/src/views/reporting/ReportingShell.vue`
