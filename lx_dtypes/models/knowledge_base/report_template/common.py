from __future__ import annotations

from typing import Any, Dict, List, TypedDict, Union

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


ReportTemplateFindingRequirementInput = Union[
    ReportTemplateFindingRequirement,
    str,
]
