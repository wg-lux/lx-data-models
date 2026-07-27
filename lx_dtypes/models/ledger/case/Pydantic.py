from __future__ import annotations

import datetime
from typing import Any

from pydantic import (
    AliasChoices,
    AwareDatetime,
    Field,
    field_validator,
    model_validator,
)

from lx_dtypes.models.base.app_base_model.pydantic.LedgerBaseModel import (
    LedgerBaseModel,
)
from lx_dtypes.models.ledger.p_examination.Pydantic import PExamination
from lx_dtypes.names import CASE_MODEL_LIST_TYPE_FIELDS, CASE_MODEL_NESTED_FIELDS

from .DataDict import CaseDataDict, SerializedCaseDataDict


def _as_aware_datetime(value: Any) -> Any:
    """Normalize date-like case boundaries to timezone-aware datetimes."""
    if isinstance(value, str):
        try:
            value = datetime.datetime.fromisoformat(value)
        except ValueError:
            return value
    if isinstance(value, datetime.datetime):
        return (
            value
            if value.tzinfo is not None
            else value.replace(tzinfo=datetime.timezone.utc)
        )
    if isinstance(value, datetime.date):
        return datetime.datetime.combine(
            value, datetime.time.min, tzinfo=datetime.timezone.utc
        )
    return value


class Case(LedgerBaseModel[CaseDataDict]):
    """Transient grouping of one patient's examinations during a clinical stay."""

    case_id: str
    patient: str
    admission_date: AwareDatetime
    leave_date: AwareDatetime | None = None
    patient_examinations: list[PExamination] = Field(
        default_factory=list,
        validation_alias=AliasChoices(
            "patient_examinations", "examinations", "related_examinations"
        ),
    )

    @field_validator("admission_date", "leave_date", mode="before")
    @classmethod
    def normalize_case_date(cls, value: Any) -> Any:
        return _as_aware_datetime(value)

    @model_validator(mode="after")
    def validate_group(self) -> Case:
        if self.leave_date is not None and self.leave_date < self.admission_date:
            raise ValueError("leave_date must not be earlier than admission_date")

        mismatched = [
            str(examination.uuid)
            for examination in self.patient_examinations
            if examination.patient != self.patient
        ]
        if mismatched:
            raise ValueError(
                "patient_examinations must belong to the case patient; "
                f"mismatched examination UUIDs: {', '.join(mismatched)}"
            )
        return self

    @classmethod
    def list_type_fields(cls) -> list[str]:
        return CASE_MODEL_LIST_TYPE_FIELDS

    @property
    def ddict_class(self) -> type[CaseDataDict]:
        return CaseDataDict

    @classmethod
    def nested_fields(cls) -> list[str]:
        return CASE_MODEL_NESTED_FIELDS

    @property
    def serialized_ddict_class(self) -> type[SerializedCaseDataDict]:
        return SerializedCaseDataDict

    @classmethod
    def serialized_model_class(cls) -> type[SerializedCase]:
        return SerializedCase


class SerializedCase(LedgerBaseModel[SerializedCaseDataDict]):
    case_id: str
    patient: str
    admission_date: AwareDatetime
    leave_date: AwareDatetime | None = None
    patient_examinations: str = ""

    @classmethod
    def list_type_fields(cls) -> list[str]:
        return CASE_MODEL_LIST_TYPE_FIELDS

    @property
    def ddict_class(self) -> type[SerializedCaseDataDict]:
        return SerializedCaseDataDict

    @classmethod
    def nested_fields(cls) -> list[str]:
        return []
