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
- `LX_DTYPES_FINDINGS_MODULE`
  Optional knowledge-base module name used by the findings/classification API.
  Defaults to `lx_knowledge_base`.

Example:

```python
# settings.py
LX_DTYPES_HOST_MODELS_MODULE = "endoreg_db.models"
LX_DTYPES_FINDINGS_MODULE = "report_template_examples"
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

If any are missing, API import or runtime requests will fail.

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
- Optionally set `LX_DTYPES_FINDINGS_MODULE`.
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
