from __future__ import annotations

from typing import Any, Dict, List, Literal, TypedDict, Union

from pydantic import BaseModel, Field


class ReportTemplateClassificationRequirementDataDict(TypedDict):
    classification: str
    required: bool


class ReportTemplateFindingRequirementDataDict(TypedDict):
    finding: str
    required: bool
    multiple_allowed: bool
    classifications: List[ReportTemplateClassificationRequirementDataDict]


class ReportTemplateValidatorsDataDict(TypedDict):
    examination_validators: List[str]
    findings_validators: List[str]


class FindingsValidatorQueryDataDict(TypedDict, total=False):
    finding: str
    operator: str
    params: Dict[str, Any]


class ReportTemplateSectionFieldDataDict(TypedDict, total=False):
    key: str
    required: bool
    label: str
    source: Literal["patient", "patient_examination", "history"]


class ReportTemplateClassificationRequirement(BaseModel):
    classification: str
    required: bool = False


class ReportTemplateFindingRequirement(BaseModel):
    finding: str
    required: bool = False
    multiple_allowed: bool = False
    classifications: List[ReportTemplateClassificationRequirement] = Field(
        default_factory=list
    )


class ReportTemplateValidators(BaseModel):
    examination_validators: List[str] = Field(default_factory=list)
    findings_validators: List[str] = Field(default_factory=list)


class ReportTemplateSectionField(BaseModel):
    key: str
    required: bool = False
    label: str | None = None
    source: Literal["patient", "patient_examination", "history"] | None = None


ReportTemplateFindingRequirementInput = Union[
    ReportTemplateFindingRequirement,
    str,
]
