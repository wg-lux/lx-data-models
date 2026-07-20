from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
from typing import cast
from uuid import UUID, uuid4

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

from .json_types import JsonValue

DescriptorValue = str | int | float | bool | list[str]


class _DtypesRecordLedgerPayload(BaseModel):
    """JSON-visible fields shared by every persisted ledger node."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_default=True,
    )

    created_at: AwareDatetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    uuid: str | UUID = Field(default_factory=lambda: str(uuid4()))
    tags: str | list[str] = Field(default_factory=list)
    external_ids: dict[str, str] = Field(default_factory=dict)


class DtypesRecordClassificationChoiceDescriptorPayload(_DtypesRecordLedgerPayload):
    descriptor_value: DescriptorValue
    classification_choice_descriptor: str
    patient_finding_classification_choice: str


class DtypesRecordClassificationChoicePayload(_DtypesRecordLedgerPayload):
    classification: str
    classification_choice: str
    patient_finding_classifications: str
    patient_finding_classification_choice_descriptors: list[
        DtypesRecordClassificationChoiceDescriptorPayload
    ] = Field(default_factory=list)


class DtypesRecordClassificationGroupPayload(_DtypesRecordLedgerPayload):
    patient_finding: str
    patient_finding_classification_choices: list[
        DtypesRecordClassificationChoicePayload
    ] = Field(default_factory=list)


class DtypesRecordInterventionPayload(_DtypesRecordLedgerPayload):
    patient_finding_interventions: str
    intervention: str


class DtypesRecordInterventionGroupPayload(_DtypesRecordLedgerPayload):
    patient_finding: str
    patient_finding_interventions: list[DtypesRecordInterventionPayload] = Field(
        default_factory=list
    )


class DtypesRecordFindingPayload(_DtypesRecordLedgerPayload):
    finding: str
    patient_examination: str
    patient_finding_classifications: list[DtypesRecordClassificationGroupPayload] = (
        Field(default_factory=list)
    )
    patient_finding_interventions: list[DtypesRecordInterventionGroupPayload] = Field(
        default_factory=list
    )


class DtypesRecordIndicationClassificationDescriptorPayload(_DtypesRecordLedgerPayload):
    descriptor_value: DescriptorValue
    classification_choice_descriptor: str
    patient_indication_classification: str


class DtypesRecordIndicationClassificationPayload(_DtypesRecordLedgerPayload):
    classification: str
    classification_choice: str
    patient_indication: str
    patient_indication_classification_descriptors: list[
        DtypesRecordIndicationClassificationDescriptorPayload
    ] = Field(default_factory=list)


class DtypesRecordIndicationPayload(_DtypesRecordLedgerPayload):
    indication: str
    patient_examination: str
    patient_indication_classifications: list[
        DtypesRecordIndicationClassificationPayload
    ] = Field(default_factory=list)


class DtypesRecordPersistencePayload(_DtypesRecordLedgerPayload):
    """Complete, strict JSON contract persisted by an LXDM host application."""

    patient: str
    examiners: str | list[str] = Field(default_factory=list)
    date: AwareDatetime | None = None
    examination: str
    knowledge_base_module: str | None = None
    knowledge_base_version: str | None = None
    patient_findings: list[DtypesRecordFindingPayload] = Field(default_factory=list)
    patient_indications: list[DtypesRecordIndicationPayload] = Field(
        default_factory=list
    )


def parse_dtypes_record_persistence_payload(
    payload: Mapping[str, JsonValue] | BaseModel,
) -> DtypesRecordPersistencePayload:
    """Validate persisted JSON or a typed ledger object at the host boundary."""

    if isinstance(payload, BaseModel):
        candidate = payload.model_dump(mode="python", exclude_none=True)
    else:
        candidate = dict(payload)
    return DtypesRecordPersistencePayload.model_validate(candidate)


def dump_dtypes_record_persistence_payload(
    payload: Mapping[str, JsonValue] | BaseModel,
) -> dict[str, JsonValue]:
    """Return the canonical JSON representation suitable for a JSONField."""

    validated = parse_dtypes_record_persistence_payload(payload)
    return cast(
        dict[str, JsonValue],
        validated.model_dump(mode="json", exclude_none=True),
    )


__all__ = [
    "DescriptorValue",
    "DtypesRecordClassificationChoiceDescriptorPayload",
    "DtypesRecordClassificationChoicePayload",
    "DtypesRecordClassificationGroupPayload",
    "DtypesRecordFindingPayload",
    "DtypesRecordIndicationClassificationDescriptorPayload",
    "DtypesRecordIndicationClassificationPayload",
    "DtypesRecordIndicationPayload",
    "DtypesRecordInterventionGroupPayload",
    "DtypesRecordInterventionPayload",
    "DtypesRecordPersistencePayload",
    "dump_dtypes_record_persistence_payload",
    "parse_dtypes_record_persistence_payload",
]
