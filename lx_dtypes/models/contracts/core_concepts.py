from __future__ import annotations

from typing import Dict, List

from pydantic import BaseModel, ConfigDict, Field


class CoreConceptBase(BaseModel):
    """Canonical cross-layer entity shape for KB-driven concepts."""

    id: int | None = None
    name: str
    name_de: str | None = None
    name_en: str | None = None
    description: str | None = None
    uuid: str | None = None
    tags: List[str] = Field(default_factory=list)
    kb_module_name: str | None = None

    model_config = ConfigDict(extra="forbid")


class ClassificationCore(CoreConceptBase):
    classification_choices: List[str] = Field(default_factory=list)
    classification_types: List[str] = Field(default_factory=list)


class ClassificationChoiceCore(CoreConceptBase):
    classification_choice_descriptors: List[str] = Field(default_factory=list)


class ClassificationChoiceDescriptorCore(CoreConceptBase):
    classification_choice_descriptor_type: str | None = None
    unit: str | None = None
    numeric_min: float | None = None
    numeric_max: float | None = None
    numeric_distribution: str | None = None
    numeric_distribution_params: Dict[str, str | float | int] = Field(
        default_factory=dict
    )
    text_max_length: int | None = None
    default_value_str: str | None = None
    default_value_num: float | None = None
    default_value_bool: bool | None = None
    selection_options: List[str] = Field(default_factory=list)
    selection_multiple: bool | None = None
    selection_multiple_n_min: int | None = None
    selection_multiple_n_max: int | None = None
    selection_default_options: Dict[str, float] = Field(default_factory=dict)


class ExaminationCore(CoreConceptBase):
    findings: List[str] = Field(default_factory=list)
    examination_types: List[str] = Field(default_factory=list)
    indications: List[str] = Field(default_factory=list)


class FindingCore(CoreConceptBase):
    finding_types: List[str] = Field(default_factory=list)
    classifications: List[str] = Field(default_factory=list)
    interventions: List[str] = Field(default_factory=list)


class FindingTypeCore(CoreConceptBase):
    pass


class IndicationCore(CoreConceptBase):
    indication_types: List[str] = Field(default_factory=list)
    interventions: List[str] = Field(default_factory=list)


class IndicationTypeCore(CoreConceptBase):
    pass


class InterventionCore(CoreConceptBase):
    intervention_types: List[str] = Field(default_factory=list)


class InterventionTypeCore(CoreConceptBase):
    pass


class UnitCore(CoreConceptBase):
    abbreviation: str | None = None
    unit_types: List[str] = Field(default_factory=list)


class UnitTypeCore(CoreConceptBase):
    pass


class InformationSourceCore(CoreConceptBase):
    information_source_types: List[str] = Field(default_factory=list)


class InformationSourceTypeCore(CoreConceptBase):
    pass


class CitationCore(CoreConceptBase):
    citation_key: str
    title: str
    abstract: str | None = None
    authors: List[str] = Field(default_factory=list)
    publication_year: int | None = None
    publication_month: str | None = None
    journal: str | None = None
    publisher: str | None = None
    volume: str | None = None
    issue: str | None = None
    pages: str | None = None
    doi: str | None = None
    url: str | None = None
    entry_type: str | None = None
    language: str | None = None
    keywords: List[str] = Field(default_factory=list)
    identifiers: Dict[str, str] = Field(default_factory=dict)


class CoreConceptCollection(BaseModel):
    module_name: str
    classification: List[ClassificationCore] = Field(default_factory=list)
    classification_choice: List[ClassificationChoiceCore] = Field(default_factory=list)
    classification_choice_descriptor: List[ClassificationChoiceDescriptorCore] = (
        Field(default_factory=list)
    )
    examination: List[ExaminationCore] = Field(default_factory=list)
    finding: List[FindingCore] = Field(default_factory=list)
    finding_type: List[FindingTypeCore] = Field(default_factory=list)
    indication: List[IndicationCore] = Field(default_factory=list)
    indication_type: List[IndicationTypeCore] = Field(default_factory=list)
    intervention: List[InterventionCore] = Field(default_factory=list)
    intervention_type: List[InterventionTypeCore] = Field(default_factory=list)
    unit: List[UnitCore] = Field(default_factory=list)
    unit_type: List[UnitTypeCore] = Field(default_factory=list)
    information_source: List[InformationSourceCore] = Field(default_factory=list)
    information_source_type: List[InformationSourceTypeCore] = Field(default_factory=list)
    citation: List[CitationCore] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


__all__ = [
    "CoreConceptBase",
    "ClassificationCore",
    "ClassificationChoiceCore",
    "ClassificationChoiceDescriptorCore",
    "ExaminationCore",
    "FindingCore",
    "FindingTypeCore",
    "IndicationCore",
    "IndicationTypeCore",
    "InterventionCore",
    "InterventionTypeCore",
    "UnitCore",
    "UnitTypeCore",
    "InformationSourceCore",
    "InformationSourceTypeCore",
    "CitationCore",
    "CoreConceptCollection",
]
