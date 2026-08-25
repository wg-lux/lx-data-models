import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from lx_dtypes.factories.typed_lists import list_of_str_factory
from lx_dtypes.models.base.app_base_model.pydantic.KnowledgebaseBaseModel import (
    KnowledgebaseBaseModel,
)
from lx_dtypes.models.knowledge_base.report_template.ReportTemplateCoverage import (
    ReportTemplateCoverageConcept,
)
from lx_dtypes.models.knowledge_base.report_template.ReportTemplateDataDict import (
    ReportTemplateDataDict,
)


class ReportTemplateValidators(BaseModel):
    examination_validators: list[str] = Field(default_factory=list)
    findings_validators: list[str] = Field(default_factory=list)
    classification_validators: list[str] = Field(default_factory=list)
    intervention_validators: list[str] = Field(default_factory=list)
    unit_validators: list[str] = Field(default_factory=list)


class ReportTemplateGuidelineReference(BaseModel):
    """Versioned guideline provenance exposed with a report template."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    guideline_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    issuing_organization: str = Field(min_length=1)
    version: str = Field(min_length=1)
    publication_date: datetime.date
    canonical_url: str = Field(min_length=1)
    cited_sections: list[str] = Field(min_length=1)

    @field_validator("canonical_url")
    @classmethod
    def require_https_url(cls, value: str) -> str:
        if not value.startswith("https://"):
            raise ValueError("guideline canonical_url must use HTTPS")
        return value


class ReportTemplate(KnowledgebaseBaseModel[ReportTemplateDataDict]):
    examination: str
    version: str | None = None
    guideline_references: list[ReportTemplateGuidelineReference] = Field(
        default_factory=list
    )
    coverage_version: str | None = None
    coverage_concepts: list[ReportTemplateCoverageConcept] = Field(default_factory=list)
    report_sections: str | list[str] = Field(default_factory=list_of_str_factory)
    validators: ReportTemplateValidators = Field(
        default_factory=ReportTemplateValidators
    )

    @classmethod
    def list_type_fields(cls) -> list[str]:
        return ["report_sections"]

    @property
    def ddict_class(self) -> type[ReportTemplateDataDict]:
        return ReportTemplateDataDict
