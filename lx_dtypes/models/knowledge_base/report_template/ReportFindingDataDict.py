from typing import NotRequired, TypedDict

from lx_dtypes.models.base.app_base_model.ddict.KnowledgebaseBaseModelDataDict import (
    KnowledgebaseBaseModelDataDict,
)


class ReportTemplateClassificationRequirementDataDict(TypedDict):
    """Serialized :class:`ReportTemplateClassificationRequirement`."""

    classification: str
    required: bool
    concept_id: NotRequired[str | None]
    applicability_rule: NotRequired[str | None]


class ReportTemplateFindingRequirementDataDict(TypedDict):
    """Serialized :class:`ReportTemplateFindingRequirement`."""

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
    """Serialized :class:`ReportFinding` knowledge-base record."""
