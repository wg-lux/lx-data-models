from typing import List, TypedDict

from lx_dtypes.models.base.app_base_model.ddict.KnowledgebaseBaseModelDataDict import (
    KnowledgebaseBaseModelDataDict,
)


class ReportTemplateClassificationRequirementDataDict(TypedDict):
    classification: str
    required: bool


class ReportTemplateFindingRequirementDataDict(TypedDict):
    finding: str
    required: bool
    multiple_allowed: bool
    classifications: List[ReportTemplateClassificationRequirementDataDict]


class ReportFindingDataDict(
    KnowledgebaseBaseModelDataDict,
    ReportTemplateFindingRequirementDataDict,
):
    pass
