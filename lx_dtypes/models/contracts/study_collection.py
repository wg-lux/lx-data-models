"""Typed study observations; hosts own assessment, linkage and transactions."""

import json
from typing import Self
from uuid import UUID

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    ValidationInfo,
    ValidatorFunctionWrapHandler,
    field_validator,
    model_validator,
)

from lx_dtypes.language import DEFAULT_LANGUAGE, LanguageCode

from .cohort_definition import CohortDefinition
from .dtypes_record_persistence import (
    DtypesRecordPersistencePayload,
    parse_dtypes_record_persistence_payload,
)
from .knowledge_base import KnowledgeBaseIdentity
from .study import StudyDefinition
from .validation import ValidationReport


class StudyCollectionRecord(BaseModel):
    """A ledger observation and its server-computed, version-pinned assessment."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    record_uuid: UUID
    study_uuid: UUID
    study_definition: StudyDefinition
    cohort_uuid: UUID | None = None
    cohort_definition: CohortDefinition | None = None
    patient_examination_uuid: UUID
    package_snapshot_id: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    record: DtypesRecordPersistencePayload
    evaluation: ValidationReport
    report_template_name: str | None = Field(default=None, min_length=1)
    evaluated_at: AwareDatetime
    language: LanguageCode = DEFAULT_LANGUAGE

    @field_validator("study_definition", "cohort_definition", mode="before")
    @classmethod
    def reparse_definitions(cls, value: object) -> object:
        return (
            value.model_dump(round_trip=True) if isinstance(value, BaseModel) else value
        )

    @field_validator("record", mode="after")
    @classmethod
    def revalidate_record(
        cls, value: DtypesRecordPersistencePayload
    ) -> DtypesRecordPersistencePayload:
        # Nested models are mutable; never trust a previously parsed instance.
        return parse_dtypes_record_persistence_payload(value)

    @field_validator("evaluation", mode="wrap")
    @classmethod
    def revalidate_evaluation(
        cls, value: object, handler: ValidatorFunctionWrapHandler, info: ValidationInfo
    ) -> ValidationReport:
        if isinstance(value, ValidationReport):
            value = value.model_dump(round_trip=True)
        supplied_ok: object = None
        if isinstance(value, dict) and "ok" in value:
            value = value.copy()
            supplied_ok = value.pop("ok")
            if not isinstance(supplied_ok, bool):
                raise ValueError("evaluation.ok must be a boolean")
        result: ValidationReport = (
            ValidationReport.model_validate_json(json.dumps(value))
            if info.mode == "json"
            else handler(value)
        )
        if supplied_ok is not None and supplied_ok != result.ok:
            raise ValueError("evaluation.ok conflicts with its issues")
        return result

    @model_validator(mode="after")
    def consistent_assessment(self) -> Self:
        if (self.cohort_uuid is None) != (self.cohort_definition is None):
            raise ValueError("cohort identity and definition must be supplied together")
        identity = KnowledgeBaseIdentity.model_validate(
            {
                "knowledge_base_module": self.record.knowledge_base_module,
                "knowledge_base_version": self.record.knowledge_base_version,
            }
        )
        if identity != self.evaluation.knowledge_base_identity:
            raise ValueError("record and evaluation must share the exact KB identity")
        if self.report_template_name is not None and (
            self.report_template_name != self.report_template_name.strip()
        ):
            raise ValueError(
                "report_template_name must not have surrounding whitespace"
            )
        if self.evaluation.study_evaluated != (self.report_template_name is not None):
            raise ValueError("study evaluation requires its report template provenance")
        if not self.evaluation.study_evaluated and any(
            issue.source == "study" for issue in self.evaluation.issues
        ):
            raise ValueError("study issues require a completed study evaluation")
        if any(
            issue.level == "error" and issue.source != "study"
            for issue in self.evaluation.issues
        ):
            raise ValueError("contract and terminology errors prevent collection")
        return self


__all__ = ["StudyCollectionRecord"]
