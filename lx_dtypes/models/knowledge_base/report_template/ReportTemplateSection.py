from typing import Literal, Self

from pydantic import Field, model_validator

from lx_dtypes.models.base.app_base_model.pydantic.KnowledgebaseBaseModel import (
    KnowledgebaseBaseModel,
)
from lx_dtypes.models.knowledge_base.report_template.ReportFinding import (
    ReportTemplateFindingRequirement,
)
from lx_dtypes.models.knowledge_base.report_template.ReportTemplateSectionDataDict import (
    ReportTemplateSectionDataDict,
)
from lx_dtypes.models.model import DtypesModel


class ReportTemplateSectionField(DtypesModel):
    """Non-finding data field shown in a report section.

    Attributes:
        key: Field identifier, for example ``"examination_date"``.
        required: Whether the field must be filled.
        label: Optional display label.
        source: Host data source that provides the value.
    """

    key: str
    required: bool = False
    label: str | None = None
    source: Literal["patient", "patient_examination", "history"] | None = None


class ReportTemplateSection(KnowledgebaseBaseModel[ReportTemplateSectionDataDict]):
    """Knowledge-base record for one section of a report template.

    Attributes:
        title_de: German title; defaults to ``name_de`` or ``name``.
        title_en: English title; defaults to ``name_en`` or ``name``.
        position: Sort position within the report.
        types: Section type tags.
        section_kind: Kind of content the section holds.
        fields: Non-finding data fields, for patient-data or history sections.
        findings: Expected findings, inline or by :class:`ReportFinding` name.
    """

    title_de: str = ""
    title_en: str = ""
    position: int = 0
    types: list[str] = Field(default_factory=list)
    section_kind: Literal["findings", "patient_data", "history", "medications"] = (
        "findings"
    )
    fields: list[ReportTemplateSectionField] = Field(default_factory=list)
    findings: list[ReportTemplateFindingRequirement | str] = Field(default_factory=list)

    @model_validator(mode="after")
    def guarantee_localized_titles(self) -> Self:
        """Always expose localized titles; legacy sections fall back upstream."""

        if not self.title_de:
            self.title_de = (
                self.name_de
                if self.name_de and self.name_de != "unknown"
                else self.name
            )
        if not self.title_en:
            self.title_en = (
                self.name_en
                if self.name_en and self.name_en != "unknown"
                else self.name
            )
        return self

    @classmethod
    def list_type_fields(cls) -> list[str]:
        """Return fields stored as lists; sections have none."""
        return []

    @property
    def ddict_class(self) -> type[ReportTemplateSectionDataDict]:
        """Typed dictionary class used for serialization."""
        return ReportTemplateSectionDataDict
