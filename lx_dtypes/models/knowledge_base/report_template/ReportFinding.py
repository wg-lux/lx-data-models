from typing import Literal

from pydantic import BaseModel, Field

from lx_dtypes.models.base.app_base_model.pydantic.KnowledgebaseBaseModel import (
    KnowledgebaseBaseModel,
)
from lx_dtypes.models.knowledge_base.report_template.ReportFindingDataDict import (
    ReportFindingDataDict,
)


class ReportTemplateClassificationRequirement(BaseModel):
    classification: str
    required: bool = False
    concept_id: str | None = None
    applicability_rule: str | None = None
    applicability_status: (
        Literal["required", "conditional", "not_applicable"] | None
    ) = None
    applicability_reason: str | None = None


class ReportTemplateFindingRequirement(BaseModel):
    finding: str
    required: bool = False
    multiple_allowed: bool = False
    concept_id: str | None = None
    applicability_rule: str | None = None
    applicability_status: (
        Literal["required", "conditional", "not_applicable"] | None
    ) = None
    applicability_reason: str | None = None
    classifications: list[ReportTemplateClassificationRequirement] = Field(
        default_factory=list
    )


class ReportFinding(KnowledgebaseBaseModel[ReportFindingDataDict]):
    finding: str
    required: bool = False
    multiple_allowed: bool = False
    concept_id: str | None = None
    applicability_rule: str | None = None
    applicability_status: (
        Literal["required", "conditional", "not_applicable"] | None
    ) = None
    applicability_reason: str | None = None
    classifications: list[ReportTemplateClassificationRequirement] = Field(
        default_factory=list
    )

    def as_requirement(self) -> ReportTemplateFindingRequirement:
        return ReportTemplateFindingRequirement(
            finding=self.finding,
            required=self.required,
            multiple_allowed=self.multiple_allowed,
            classifications=self.classifications,
            concept_id=self.concept_id,
            applicability_rule=self.applicability_rule,
            applicability_status=self.applicability_status,
            applicability_reason=self.applicability_reason,
        )

    @classmethod
    def list_type_fields(cls) -> list[str]:
        return []

    @property
    def ddict_class(self) -> type[ReportFindingDataDict]:
        return ReportFindingDataDict
