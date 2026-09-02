from __future__ import annotations

from collections.abc import Mapping
from typing import Literal, cast

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from .json_types import JsonObject

REPORT_DRAFT_SCHEMA_VERSION: Literal["1.0"] = "1.0"


class ReportDraftTemplateIdentity(BaseModel):
    """Stable template identity stored with an editor draft."""

    model_config = ConfigDict(
        allow_inf_nan=False,
        extra="forbid",
        strict=True,
        str_strip_whitespace=True,
    )

    module_name: str = Field(
        default="",
        validation_alias=AliasChoices("module_name", "moduleName"),
    )
    knowledge_base_version: str = Field(
        default="",
        validation_alias=AliasChoices(
            "knowledge_base_version",
            "knowledgeBaseVersion",
        ),
    )
    template_version: str = Field(
        default="",
        validation_alias=AliasChoices("template_version", "templateVersion"),
    )
    template_hash: str = Field(
        default="",
        validation_alias=AliasChoices("template_hash", "templateHash"),
    )
    lifecycle_status: str = Field(
        default="",
        validation_alias=AliasChoices("lifecycle_status", "lifecycleStatus"),
    )


class ReportDraftIndication(BaseModel):
    """One selected examination indication and optional choice."""

    model_config = ConfigDict(allow_inf_nan=False, extra="forbid", strict=True)

    examination_indication_id: int | None = Field(default=None, gt=0)
    indication_choice_id: int | None = Field(default=None, gt=0)


class ReportDraftSectionState(BaseModel):
    """Editable presentation state for one report-template section."""

    model_config = ConfigDict(allow_inf_nan=False, extra="forbid", strict=True)

    note: str = ""
    include_patient_data: bool = False
    include_examination_data: bool = False


class PatientExaminationReportDraft(BaseModel):
    """Versioned report-editor state persisted on a patient examination."""

    model_config = ConfigDict(
        allow_inf_nan=False,
        extra="forbid",
        strict=True,
        str_strip_whitespace=True,
    )

    schema_version: Literal["1.0"] = REPORT_DRAFT_SCHEMA_VERSION
    revision: int = Field(default=0, ge=0)
    module_name: str = ""
    template_name: str = ""
    template_identity: ReportDraftTemplateIdentity | None = None
    indications: list[ReportDraftIndication] = Field(default_factory=list)
    template_section_drafts: dict[str, ReportDraftSectionState] = Field(
        default_factory=dict
    )
    selected_report_language: Literal["de", "en"] = "de"
    active_report_id: int | None = Field(default=None, gt=0)
    report_text_mode: Literal["generated", "manual"] = "generated"
    rendered_text: str = ""
    payload: JsonObject = Field(default_factory=dict)


def dump_patient_examination_report_draft(
    value: Mapping[str, object] | PatientExaminationReportDraft | None,
) -> JsonObject:
    """Validate and serialize a draft to its canonical persisted JSON shape."""

    if value is None or value == {}:
        return {}
    draft = (
        value
        if isinstance(value, PatientExaminationReportDraft)
        else PatientExaminationReportDraft.model_validate(dict(value))
    )
    return cast(JsonObject, draft.model_dump(mode="json", exclude_none=True))


__all__ = [
    "REPORT_DRAFT_SCHEMA_VERSION",
    "PatientExaminationReportDraft",
    "ReportDraftIndication",
    "ReportDraftSectionState",
    "ReportDraftTemplateIdentity",
    "dump_patient_examination_report_draft",
]
