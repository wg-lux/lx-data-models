from typing import Literal

from pydantic import Field

from lx_dtypes.models.base.app_base_model.pydantic.KnowledgebaseBaseModel import (
    KnowledgebaseBaseModel,
)
from lx_dtypes.models.knowledge_base.report_template.ReportFindingDataDict import (
    ReportFindingDataDict,
)
from lx_dtypes.models.model import DtypesModel


class ReportTemplateClassificationRequirement(DtypesModel):
    """Classification that a report template expects for a finding.

    Attributes:
        classification: Classification name.
        required: Whether the classification must be documented.
        concept_id: Optional report-concept identifier for coverage reporting.
        applicability_rule: Rule that decides applicability when conditional.
        applicability_status: Explicit applicability of the requirement.
        applicability_reason: Reason when the requirement is not applicable.
    """

    classification: str
    required: bool = False
    concept_id: str | None = None
    applicability_rule: str | None = None
    applicability_status: (
        Literal["required", "conditional", "not_applicable"] | None
    ) = None
    applicability_reason: str | None = None


class ReportTemplateFindingRequirement(DtypesModel):
    """Finding that a report template section expects, with its classifications.

    Attributes:
        finding: Finding name.
        required: Whether the finding must be documented.
        multiple_allowed: Whether the finding may be documented more than once.
        classifications: Classification requirements for the finding.
    """

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
    """Reusable knowledge-base record describing a finding in a report.

    It has the same fields as :class:`ReportTemplateFindingRequirement` and
    can be referenced by name from report template sections. Use
    :meth:`as_requirement` to obtain the inline requirement form.
    """

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
        """Return this record as an inline :class:`ReportTemplateFindingRequirement`."""
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
        """Return fields stored as lists; report findings have none."""
        return []

    @property
    def ddict_class(self) -> type[ReportFindingDataDict]:
        """Typed dictionary class used for serialization."""
        return ReportFindingDataDict
