from __future__ import annotations

import pytest
from pydantic import ValidationError

from lx_dtypes.models.contracts.patient_finding_classification_runtime import (
    PatientFindingClassificationNumericalDescriptorsPayload,
    PatientFindingClassificationSubcategoriesPayload,
)


def test_patient_finding_classification_subcategories_validate_nested_shape() -> None:
    payload = PatientFindingClassificationSubcategoriesPayload.model_validate(
        {"location": {"required": True, "choices": ["cecum"], "value": "cecum"}}
    )

    assert payload.root["location"].value == "cecum"


def test_patient_finding_classification_subcategories_reject_invalid_choice_shape() -> (
    None
):
    with pytest.raises(ValidationError):
        PatientFindingClassificationSubcategoriesPayload.model_validate(
            {"location": {"choices": "cecum"}}
        )


@pytest.mark.parametrize(
    "payload",
    [
        {"location": {"choices": []}},
        {"location": {"choices": ["cecum", ""]}},
        {"location": {"choices": ["cecum", "cecum"]}},
        {"location": {"choices": ["cecum"], "value": "rectum"}},
    ],
)
def test_patient_finding_classification_subcategories_reject_invalid_choices(
    payload: dict[str, dict[str, object]],
) -> None:
    with pytest.raises(ValidationError):
        PatientFindingClassificationSubcategoriesPayload.model_validate(payload)


def test_patient_finding_classification_descriptors_validate_nested_shape() -> None:
    payload = PatientFindingClassificationNumericalDescriptorsPayload.model_validate(
        {"size": {"min": 0.0, "max": 10.0, "mean": 5.0, "std": 1.0, "value": 4.0}}
    )

    assert payload.root["size"].value == 4.0


def test_patient_finding_classification_descriptors_reject_invalid_descriptor_shape() -> (
    None
):
    with pytest.raises(ValidationError):
        PatientFindingClassificationNumericalDescriptorsPayload.model_validate(
            {"size": {"value": "large"}}
        )


@pytest.mark.parametrize(
    "payload",
    [
        {"size": {"min": 10.0, "max": 0.0, "mean": 5.0, "std": 1.0}},
        {"size": {"min": 0.0, "max": 10.0, "mean": 11.0, "std": 1.0}},
        {"size": {"min": 0.0, "max": 10.0, "mean": 5.0, "std": -1.0}},
        {"size": {"min": 0.0, "max": 10.0, "mean": 5.0, "std": 1.0, "value": 11.0}},
        {
            "size": {
                "min": 0.0,
                "max": 10.0,
                "mean": 5.0,
                "std": 1.0,
                "distribution": "triangular",
            }
        },
    ],
)
def test_patient_finding_classification_descriptors_reject_invalid_invariants(
    payload: dict[str, dict[str, object]],
) -> None:
    with pytest.raises(ValidationError):
        PatientFindingClassificationNumericalDescriptorsPayload.model_validate(payload)
