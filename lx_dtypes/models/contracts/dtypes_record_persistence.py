from __future__ import annotations

from collections.abc import Mapping

from pydantic import BaseModel, ConfigDict, Field

from .json_types import JsonValue


class DtypesRecordClassificationChoicePayload(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)

    classification: str
    classification_choice: str


class DtypesRecordClassificationGroupPayload(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)

    patient_finding_classification_choices: list[
        DtypesRecordClassificationChoicePayload
    ] = Field(default_factory=list)


class DtypesRecordInterventionPayload(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)

    patient_finding_interventions: str
    intervention: str


class DtypesRecordInterventionGroupPayload(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)

    patient_finding_interventions: list[DtypesRecordInterventionPayload] = Field(
        default_factory=list
    )


class DtypesRecordFindingPayload(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)

    finding: str
    patient_finding_classifications: list[DtypesRecordClassificationGroupPayload] = (
        Field(default_factory=list)
    )
    patient_finding_interventions: list[DtypesRecordInterventionGroupPayload] = Field(
        default_factory=list
    )


class DtypesRecordPersistencePayload(BaseModel):
    model_config = ConfigDict(extra="allow", strict=True)

    examination: str
    knowledge_base_module: str = ""
    patient_findings: list[DtypesRecordFindingPayload] = Field(default_factory=list)


def parse_dtypes_record_persistence_payload(
    payload: Mapping[str, JsonValue],
) -> DtypesRecordPersistencePayload:
    return DtypesRecordPersistencePayload.model_validate(payload)


__all__ = [
    "DtypesRecordClassificationChoicePayload",
    "DtypesRecordClassificationGroupPayload",
    "DtypesRecordFindingPayload",
    "DtypesRecordInterventionGroupPayload",
    "DtypesRecordInterventionPayload",
    "DtypesRecordPersistencePayload",
    "parse_dtypes_record_persistence_payload",
]
