from typing import NotRequired, TypedDict

from lx_dtypes.models.base.app_base_model.ddict.KnowledgebaseBaseModelDataDict import (
    KnowledgebaseBaseModelDataDict,
)


class ReportTemplateClassificationRequirementDataDict(TypedDict):
    classification: str
    required: bool
    concept_id: NotRequired[str | None]
    applicability_rule: NotRequired[str | None]


class ReportTemplateFindingRequirementDataDict(TypedDict):
    finding: str
    required: bool
    multiple_allowed: bool
    classifications: list[ReportTemplateClassificationRequirementDataDict]
    concept_id: NotRequired[str | None]
    applicability_rule: NotRequired[str | None]


class ReportFindingDataDict(
    KnowledgebaseBaseModelDataDict,
    ReportTemplateFindingRequirementDataDict,
):
    pass
