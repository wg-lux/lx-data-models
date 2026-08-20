# Django Host Integration Contract

This guide defines the supported integration contract for embedding
`lx_dtypes.django.api` into a host Django application.

Use this guide when:

- you want to mount the `lx_dtypes` API in another Django project
- you need the minimum required host ORM models
- you want to know which settings and environment variables are mandatory

This is a contract document, not an internal implementation walkthrough.

## Required Settings

The host project must configure:

- `LX_DTYPES_HOST_MODELS_MODULE`
  Python import path to a module that exports the required Django ORM models.
- `LX_DTYPES_KB_REGISTRY`
  Path to the versioned registry containing an explicit active module and
  version. Findings, classifications, templates, and validation all resolve
  through this identity.
- `LX_DTYPES_TERMINOLOGY_IMPORT_ROOT` (optional)
  Base path for uploaded KB ZIP extraction.
  Defaults to `<registry parent>/terminology-packages`.

Before starting Django, run the strict package-owned bootstrap boundary:

```bash
lx-dtypes-kb-registry bootstrap
```

The command reads `LX_DTYPES_KB_REGISTRY`, provisions every packaged provider
identity, selects the packaged default only when no active identity exists, and
fully loads every packaged bundle. Django startup does not silently seed or
repair registry state. Bootstrap failure must block service startup.

Example:

```python
# settings.py
LX_DTYPES_HOST_MODELS_MODULE = "endoreg_db.models"
LX_DTYPES_KB_REGISTRY = "/var/lib/host/terminology/registry.json"
LX_DTYPES_TERMINOLOGY_IMPORT_ROOT = "/var/lib/host/terminology/terminology-packages"
```

## URL Mounting

Mount the API by including `lx_dtypes.django.urls` or by exposing
`lx_dtypes.django.api.main.api.urls` directly.

Example:

```python
from django.urls import include, path

urlpatterns = [
    path("", include("lx_dtypes.django.urls")),
]
```

The shipped URL config exposes the API under `base_api/`.

## Required Exported ORM Models

The module referenced by `LX_DTYPES_HOST_MODELS_MODULE` must export these names:

- `Examination`
- `Finding`
- `FindingClassification`
- `FindingClassificationChoice`
- `PatientExamination`
- `PatientFinding`
- `PatientFindingClassification`

If any required model export is missing, API import or runtime requests fail.

For state-changing patient-finding routes it must also export:

- `authenticate_request_user(request)`
  Resolves an authenticated Django session principal or validates a Bearer token.
  It must return `None` for missing or invalid credentials.
- `patient_finding_access_allowed(request, patient_finding)`
  Performs object-level authorization. It must return `False` for users without
  a center assignment and for findings outside the user's center. Staff or
  superusers may be granted cross-center access by the host policy.
- `patient_examination_access_allowed(request, patient_examination)`
  Applies the same object-level policy before a finding can be created for an
  examination.
- `patient_findings_queryset_for_request(request)`
  Returns only active findings visible to the authenticated principal. It must
  return an empty queryset for anonymous or unscoped users.

Patient-finding list, create, patch, classification and delete routes require an
authenticated principal and fail closed when the corresponding authorization
callback is absent. Foreign-center objects return 404, while list responses are
filtered to the caller's center. Deactivation records the authenticated actor
and server timestamp. Each mutation refreshes the persisted LXDM record in the
same database transaction.

## Persisted LXDM Record Contract

Hosts must treat
`lx_dtypes.models.contracts.DtypesRecordPersistencePayload` as the canonical
type for the JSON record attached to an examination. Import
`parse_dtypes_record_persistence_payload` at input and storage boundaries and
`dump_dtypes_record_persistence_payload` when writing a JSON field. Do not copy
the schema into a host serializer or maintain a reduced dictionary shape.

The contract is the complete `PExamination` ledger graph: patient and examiner
references, examination identity, knowledge-base module/version, findings,
classifications, choices and descriptors, interventions, and indications.
Unknown fields are rejected at every nested level. Host-only database IDs and
authorization data are not accepted from this payload; the host resolves those
from the authenticated request and URL-scoped examination.

Before persistence, the host must additionally verify that:

- `payload.examination` equals the host examination name;
- every finding's `patient_examination` equals the URL/model examination ID;
- knowledge-base module/version are installed and supported by the deployment.

The persistence contract is public starting with `lx-dtypes` 0.2.1. A host
using the strict contract must require `lx-dtypes>=0.2.1,<0.3`. Patch releases
may add helpers but do not add required JSON fields. A new required field,
changed field meaning, or incompatible nested shape requires a minor release;
hosts must reject unsupported versions until their adapter and backfill have
been tested.

## Required Model Contract

`lx_dtypes` does not require your models to inherit from package-owned Django
base classes. It only depends on a narrow set of fields, relations, and methods.

### `Examination`

Required:

- `id`
- `name`
- `get_available_findings()`

`get_available_findings()` must return an iterable/queryset of `Finding` objects
that are valid for that examination.

### `Finding`

Required:

- `id`
- `name`
- `description`
- `finding_classifications`

`finding_classifications` must support:

- `.all()`
- `.prefetch_related("choices", "classification_types")`
- `.filter(id=...)`

### `FindingClassification`

Required:

- `id`
- `name`
- `description`
- `classification_types`
- `choices`

`classification_types` must support `.all()`.

`choices` must support:

- `.all()`
- `.filter(id=...)`

### `FindingClassificationChoice`

Required:

- `id`
- `name`
- `description`
- `subcategories`
- `numerical_descriptors`

### `PatientExamination`

Required:

- `id`
- `knowledge_base_module` or empty value
- `knowledge_base_version` or empty value
- `examiners`
- `patient_id` or `patient.pk`
- `examination_safe` or `examination`

The effective examination object must expose:

- `name`
- `get_available_findings()`

`examiners` may be a Django relation with `.all()` or a plain list-like object.

### `PatientFinding`

Required fields:

- `id`
- `patient_examination`
- `patient_examination_id`
- `finding`
- `finding_id`
- `is_active`
- `created_at`
- `updated_at`
- `deactivated_at`
- `deactivated_by`

Required manager/queryset behavior:

- `objects.filter(...)`
- `.select_related("patient_examination", "finding")`
- `.first()`
- iteration over filtered querysets

Required relations:

- `classifications`

`classifications` must support:

- `.all().delete()`
- `.filter(is_active=True)`
- `.select_related("classification", "classification_choice")`

The model should also enforce your host application's uniqueness and lifecycle
rules for active findings. `lx_dtypes` will not create those constraints for you.

### `PatientFindingClassification`

Required create fields:

- `finding`
- `classification`
- `classification_choice`
- `is_active`

Required read fields:

- `id`
- `classification`
- `classification_id`
- `classification_choice`
- `classification_choice_id`
- `subcategories`
- `numerical_descriptors`
- `is_active`

## Behavioral Assumptions

The API assumes the host application owns persistence and business rules.

Specifically:

- `PatientFinding` lifecycle is implemented by the host model.
- every patient-finding read or mutation is authenticated and host-scoped
- uniqueness of active findings per examination is enforced by the host DB/model
- `examination_safe` is preferred when present, then `examination`
- active classifications are identified with `is_active=True`
- host primary keys are stable integer-like identifiers accepted by Django ORM filtering

## What `lx_dtypes` Validates

The package validates:

- whether a requested finding is allowed for the selected examination
- whether a classification belongs to the selected finding
- whether a classification choice belongs to the selected classification
- whether those concepts are also present in the selected `lx_dtypes` knowledge-base module

The package does not validate:

- your host model migrations
- your DB constraints
- your auth model
- your custom auditing fields
- your admin integration

## EndoReg Patient Medical Ledger

`lx_dtypes.models.ledger.medical` provides typed, persistence-independent
ledger records for the patient-owned medical models in
`endoreg_db.models.medical.patient`:

- `PatientDisease`
- `PatientEvent`
- `PatientLabSample` and its nested `PatientLabValue` records
- `PatientMedication`
- `PatientMedicationSchedule` and its nested medications
- `PatientMedicalLedger`, the aggregate patient medical graph

The adapter functions accept loaded EndoReg model instances but deliberately
do not import `endoreg_db`. EndoReg remains the owner of database fields,
constraints, query planning, and lifecycle behavior; `lx_dtypes` owns only the
validated cross-repository representation.

Build the aggregate at a service boundary after loading the required
relationships:

```python
from lx_dtypes.models.ledger.medical import build_patient_medical_ledger

ledger = build_patient_medical_ledger(
    patient,
    diseases=patient.diseases.prefetch_related("classification_choices"),
    events=patient.events.select_related("event", "classification_choice"),
    lab_samples=patient.lab_samples.select_related("sample_type").prefetch_related(
        "values__lab_value",
        "values__unit",
    ),
    lab_values=patient.lab_values.select_related("lab_value", "sample", "unit"),
    medications=patient.patientmedication_set.select_related(
        "medication",
        "medication_indication",
        "unit",
    ).prefetch_related("intake_times"),
    medication_schedules=patient.patientmedicationschedule_set.prefetch_related(
        "medication__medication",
        "medication__medication_indication",
        "medication__unit",
        "medication__intake_times",
    ),
)
```

Adapters fail loudly for missing required relations, invalid dates/timestamps,
or non-JSON clinical payloads. EndoReg primary keys are retained in
`external_ids["endoreg_db"]`, and the corresponding ledger UUID is derived
deterministically from the model name and primary key. Callers must load
relations before conversion; the adapters do not issue or hide database
queries. Patient and sample links use primary keys only; patient names and
other identifying demographics are never copied into this medical ledger
graph.

## Minimal Host Module Sketch

```python
# myapp/models.py
from .medical import (
    Examination,
    Finding,
    FindingClassification,
    FindingClassificationChoice,
    PatientExamination,
    PatientFinding,
    PatientFindingClassification,
)

__all__ = [
    "Examination",
    "Finding",
    "FindingClassification",
    "FindingClassificationChoice",
    "PatientExamination",
    "PatientFinding",
    "PatientFindingClassification",
]
```

## Integration Checklist

- Set `LX_DTYPES_HOST_MODELS_MODULE`.
- Set `LX_DTYPES_KB_REGISTRY` and provision a loadable active identity.
- Export the seven required ORM model names from that module.
- Ensure `Examination.get_available_findings()` returns host `Finding` instances.
- Ensure `PatientFinding.classifications` exposes active classification rows.
- Mount `lx_dtypes.django.urls`.
- Run the API tests in your host project against your own models.

## Stability Statement

The intended stable contract is:

- settings names
- exported model names
- the required field/relation surface listed above
- URL prefix and response behavior documented by the API tests

Everything else should be treated as internal implementation detail unless
documented here.
