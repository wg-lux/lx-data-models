# Shared Study Protocol Metadata

Owner: lx_dtypes maintainers. This guide owns the `StudyMetadata` contract
(`lx_dtypes.models.contracts.study_metadata.StudyMetadata`): its fields, its
validation, and how hosts evaluate it.

## Where metadata is used

Three documents carry `study_metadata`:

- `StudyPreset.study_metadata` in `lx_dtypes.models.knowledge_base.study_preset`
- `CohortDefinitionFields.study_metadata` in `lx_dtypes.models.contracts.cohort_definition`
- each entry of `StudySetupDefinition.cohorts` in `lx_dtypes.models.contracts.study_setup`

## Boundaries

- `lx-dtypes` validates structure and declared references. Hosts resolve
  terminology and evaluate patient eligibility.
- A `StudyPreset` remains a knowledge-base record. A `StudySetupDefinition`
  remains a separate, portable configuration document.
- Metadata never grants center access, imports patient data, activates
  packages, or chooses host filesystem paths.

## Fields

| Field | Identity | Contents and validation |
| --- | --- | --- |
| `label_presentation` | — | Optional annotation label display configuration. See [Label presentation](#label-presentation). |
| `participating_centers` | `center_key` | Stable center key and human-readable name. Duplicate keys are rejected. |
| `age_groups` | `name` | Integer `minimum_age` and optional `maximum_age`, inclusive, between 0 and 150. Reversed bounds, duplicate names, booleans, and numeric strings are rejected. |
| `terminology_requirements` | `module`, `version` | Exact package identities. Several versions of the same module are permitted. |
| `inclusion_criteria` | `name` | A named criterion with an optional description and one or more concept references. |

Each inclusion-criterion concept reference has the fields `module`, `version`,
`kind`, and `name`. `kind` is `examination` or `finding`. Every concept must
name a declared terminology requirement, and duplicate references are
rejected.

## Label presentation

`label_presentation` configures how annotation labels are displayed for a
study. When it is absent or `null`, hosts show the unscoped label catalog.

- `labels` is an ordered list of canonical label `name` references, each with
  an optional `display_name` and a six-digit hex `color`.
- `scopes` is an ordered list of presentation groups for different levels of
  expertise. Each scope has a unique `name`, a `display_name`, and an ordered
  list of `labels` that must reference configured labels.
- `locked: true` makes the configured label names the allowed-label whitelist
  for requests explicitly scoped to this study. An empty locked list allows no
  new label assignments.

The following example is validated by the test suite:

```{literalinclude} ../examples/study_metadata/label_presentation.yml
:language: yaml
```

Label presentation never changes identities or permissions:

- Display names and colors never change canonical annotation or prediction
  identities.
- Scopes organize presentation. They are not roles and do not grant
  authorization.
- Selecting a study is optional. Unscoped annotation is unchanged, and
  existing annotations remain visible.
- Hosts enforce the whitelist when labels are assigned, resolve references
  against their own catalog, and keep their access checks.

## Host evaluation

Hosts such as lx-annotate evaluate metadata as follows:

| Aspect | Rule |
| --- | --- |
| Criteria | All criteria are required. Concept references inside one criterion are alternatives. |
| Terminology version | Use the module and version recorded on the examination, never the currently active terminology inferred from a name. |
| Finding evidence | An active `PatientFinding` that belongs to the same examination. |
| Age | Completed years at examination start, from the stored birth date. A missing date fails an age constraint. |
| Age groups | Alternative inclusive ranges. A February 29 birthday is reached on March 1 in non-leap years. |
| Centers | Restrict the patient-center scope the user is already authorized for to the participating keys. |
| Dependencies | Saving and previewing require all declared packages and concepts to resolve locally. |

## Compatibility

- Metadata is optional for existing cohorts and presets. Empty metadata adds
  no eligibility restrictions.
- Portable documents are parsed by
  `lx_dtypes.utils.study_setup_yaml.parse_study_setup_yaml`.
- Consumers must install a version that contains this contract. Older parsers
  reject the new fields.
- Host importers must explicitly preserve and evaluate this metadata before
  claiming operational compatibility.
