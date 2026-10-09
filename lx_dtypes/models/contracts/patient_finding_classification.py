from __future__ import annotations

from collections.abc import Mapping
from typing import TypedDict

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, PositiveInt


class PatientFindingClassificationCreateData(TypedDict):
    patient_finding_id: int
    classification_id: int
    classification_choice_id: int


class PatientFindingClassificationCreatePayload(BaseModel):
    """Create payload for patient finding classification links.

    The canonical lx_dtypes finding route names are ``classification`` and
    ``choice``. Legacy endoreg REST callers may still send the ``*_id`` names.
    """

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    patient_finding: PositiveInt = Field(
        validation_alias=AliasChoices("patient_finding", "patient_finding_id"),
    )
    classification: PositiveInt = Field(
        validation_alias=AliasChoices("classification", "classification_id"),
    )
    choice: PositiveInt = Field(
        validation_alias=AliasChoices("choice", "classification_choice_id"),
    )


def dump_patient_finding_classification_create_payload(
    payload: PatientFindingClassificationCreatePayload,
) -> PatientFindingClassificationCreateData:
    data: PatientFindingClassificationCreateData = {
        "patient_finding_id": payload.patient_finding,
        "classification_id": payload.classification,
        "classification_choice_id": payload.choice,
    }
    return data


def validate_patient_finding_classification_create_payload(
    payload: Mapping[str, int],
) -> PatientFindingClassificationCreatePayload:
    return PatientFindingClassificationCreatePayload.model_validate(dict(payload))


__all__ = [
    "PatientFindingClassificationCreateData",
    "PatientFindingClassificationCreatePayload",
    "dump_patient_finding_classification_create_payload",
    "validate_patient_finding_classification_create_payload",
]
