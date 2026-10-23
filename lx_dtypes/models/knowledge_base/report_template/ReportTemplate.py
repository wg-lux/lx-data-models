import datetime
import json

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator

from lx_dtypes.factories.typed_lists import list_of_str_factory
from lx_dtypes.models.base.app_base_model.pydantic.KnowledgebaseBaseModel import (
    KnowledgebaseBaseModel,
)
from lx_dtypes.models.knowledge_base.report_template.ReportTemplateCoverage import (
    ReportTemplateCoverageConcept,
)
from lx_dtypes.models.knowledge_base.report_template.ReportTemplateDataDict import (
    ReportTemplateDataDict,
    ReportVerbosity,
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
    verbosity_options: list[ReportVerbosity] = Field(
        default_factory=lambda: ["standard"]
    )
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

    @field_validator("guideline_references", mode="before")
    @classmethod
    def parse_json_guideline_references(
        cls, value: object, info: ValidationInfo
    ) -> object:
        # The inherited list-normalization validator materializes JSON objects
        # as Python dictionaries. Restore JSON semantics for strict native dates
        # without accepting string dates at the Python construction boundary.
        if info.mode == "json" and isinstance(value, list):
            return [
                ReportTemplateGuidelineReference.model_validate_json(json.dumps(item))
                for item in value
            ]
        return value

    @classmethod
    def list_type_fields(cls) -> list[str]:
        return ["report_sections"]

    @field_validator("verbosity_options")
    @classmethod
    def validate_verbosity_options(
        cls, value: list[ReportVerbosity]
    ) -> list[ReportVerbosity]:
        if "standard" not in value or len(set(value)) != len(value):
            raise ValueError("verbosity_options must be unique and include standard")
        return value

    @property
    def ddict_class(self) -> type[ReportTemplateDataDict]:
        return ReportTemplateDataDict
