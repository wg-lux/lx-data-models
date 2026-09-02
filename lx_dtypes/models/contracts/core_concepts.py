from __future__ import annotations

from math import isfinite
from typing import ClassVar, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .knowledge_base import validate_optional_knowledge_base_identity


class CoreConceptBase(BaseModel):
    """Canonical cross-layer entity shape for KB-driven concepts."""

    id: int | None = Field(default=None, gt=0)
    name: str = Field(min_length=1)
    name_de: str | None = None
    name_en: str | None = None
    description: str | None = None
    uuid: str | None = None
    tags: list[str] = Field(default_factory=list)
    kb_module_name: str | None = None

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_default=True,
        revalidate_instances="always",
    )

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, values: list[str]) -> list[str]:
        return _validate_names(values, field_name="tags")


class ClassificationCore(CoreConceptBase):
    classification_choices: list[str] = Field(default_factory=list)
    classification_types: list[str] = Field(default_factory=list)

    @field_validator("classification_choices", "classification_types")
    @classmethod
    def validate_references(cls, values: list[str]) -> list[str]:
        return _validate_names(values, field_name="classification references")


class ClassificationTypeCore(CoreConceptBase):
    pass


class ClassificationChoiceCore(CoreConceptBase):
    classification_choice_descriptors: list[str] = Field(default_factory=list)

    @field_validator("classification_choice_descriptors")
    @classmethod
    def validate_references(cls, values: list[str]) -> list[str]:
        return _validate_names(values, field_name="classification choice descriptors")


class ClassificationChoiceDescriptorCore(CoreConceptBase):
    classification_choice_descriptor_type: str | None = None
    unit: str | None = None
    numeric_min: float | None = None
    numeric_max: float | None = None
    numeric_distribution: str | None = None
    numeric_distribution_params: dict[str, str | float | int] = Field(
        default_factory=dict
    )
    text_max_length: int | None = Field(default=None, gt=0)
    default_value_str: str | None = None
    default_value_num: float | None = None
    default_value_bool: bool | None = None
    selection_options: list[str] = Field(default_factory=list)
    selection_multiple: bool | None = None
    selection_multiple_n_min: int | None = Field(default=None, ge=0)
    selection_multiple_n_max: int | None = Field(default=None, ge=0)
    selection_default_options: dict[str, float] = Field(default_factory=dict)

    @field_validator("numeric_min", "numeric_max", "default_value_num")
    @classmethod
    def validate_finite_numeric_value(cls, value: float | None) -> float | None:
        if value is not None and not isfinite(value):
            raise ValueError("descriptor numeric values must be finite")
        return value

    @field_validator("numeric_distribution_params")
    @classmethod
    def validate_finite_distribution_params(
        cls, values: dict[str, str | float | int]
    ) -> dict[str, str | float | int]:
        for key, value in values.items():
            if isinstance(value, float) and not isfinite(value):
                raise ValueError(f"numeric_distribution_params.{key} must be finite")
        return values

    @field_validator("selection_default_options")
    @classmethod
    def validate_selection_probabilities(
        cls, values: dict[str, float]
    ) -> dict[str, float]:
        for option, probability in values.items():
            if not isfinite(probability) or not 0 <= probability <= 1:
                raise ValueError(
                    f"selection_default_options.{option} must be between 0 and 1"
                )
        return values

    @model_validator(mode="after")
    def validate_descriptor_bounds(self) -> Self:
        if (
            self.numeric_min is not None
            and self.numeric_max is not None
            and self.numeric_min > self.numeric_max
        ):
            raise ValueError("numeric_min must not exceed numeric_max")
        if (
            self.selection_multiple_n_min is not None
            and self.selection_multiple_n_max is not None
            and self.selection_multiple_n_min > self.selection_multiple_n_max
        ):
            raise ValueError(
                "selection_multiple_n_min must not exceed selection_multiple_n_max"
            )
        unknown_defaults = sorted(
            set(self.selection_default_options) - set(self.selection_options)
        )
        if unknown_defaults:
            raise ValueError(
                "selection_default_options contains unknown options: "
                f"{', '.join(unknown_defaults)}"
            )
        return self


class ExaminationCore(CoreConceptBase):
    findings: list[str] = Field(default_factory=list)
    examination_types: list[str] = Field(default_factory=list)
    indications: list[str] = Field(default_factory=list)

    @field_validator("findings", "examination_types", "indications")
    @classmethod
    def validate_references(cls, values: list[str]) -> list[str]:
        return _validate_names(values, field_name="examination references")


class KnowledgeBaseExaminationTypeCore(CoreConceptBase):
    pass


class FindingCore(CoreConceptBase):
    finding_types: list[str] = Field(default_factory=list)
    classifications: list[str] = Field(default_factory=list)
    interventions: list[str] = Field(default_factory=list)
    caused_by_interventions: list[str] = Field(default_factory=list)

    @field_validator(
        "finding_types",
        "classifications",
        "interventions",
        "caused_by_interventions",
    )
    @classmethod
    def validate_references(cls, values: list[str]) -> list[str]:
        return _validate_names(values, field_name="finding references")


class FindingTypeCore(CoreConceptBase):
    pass


class IndicationCore(CoreConceptBase):
    indication_types: list[str] = Field(default_factory=list)
    classifications: list[str] = Field(default_factory=list)
    interventions: list[str] = Field(default_factory=list)

    @field_validator("indication_types", "classifications", "interventions")
    @classmethod
    def validate_references(cls, values: list[str]) -> list[str]:
        return _validate_names(values, field_name="indication references")


class IndicationTypeCore(CoreConceptBase):
    pass


class InterventionCore(CoreConceptBase):
    intervention_types: list[str] = Field(default_factory=list)

    @field_validator("intervention_types")
    @classmethod
    def validate_references(cls, values: list[str]) -> list[str]:
        return _validate_names(values, field_name="intervention types")


class InterventionTypeCore(CoreConceptBase):
    pass


class UnitCore(CoreConceptBase):
    abbreviation: str | None = None
    unit_types: list[str] = Field(default_factory=list)

    @field_validator("unit_types")
    @classmethod
    def validate_references(cls, values: list[str]) -> list[str]:
        return _validate_names(values, field_name="unit types")


class UnitTypeCore(CoreConceptBase):
    pass


class InformationSourceCore(CoreConceptBase):
    information_source_types: list[str] = Field(default_factory=list)

    @field_validator("information_source_types")
    @classmethod
    def validate_references(cls, values: list[str]) -> list[str]:
        return _validate_names(values, field_name="information source types")


class InformationSourceTypeCore(CoreConceptBase):
    pass


class CitationCore(CoreConceptBase):
    citation_key: str = Field(min_length=1)
    title: str = Field(min_length=1)
    abstract: str | None = None
    authors: list[str] = Field(default_factory=list)
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
    keywords: list[str] = Field(default_factory=list)
    identifiers: dict[str, str] = Field(default_factory=dict)


class CoreConceptCollection(BaseModel):
    """Complete, internally consistent terminology snapshot for API consumers."""

    module_name: str = Field(min_length=1)
    knowledge_base_module: str | None = Field(default=None, min_length=1)
    knowledge_base_version: str | None = Field(default=None, min_length=1)
    classification: list[ClassificationCore] = Field(default_factory=list)
    classification_type: list[ClassificationTypeCore] = Field(default_factory=list)
    classification_choice: list[ClassificationChoiceCore] = Field(default_factory=list)
    classification_choice_descriptor: list[ClassificationChoiceDescriptorCore] = Field(
        default_factory=list
    )
    examination: list[ExaminationCore] = Field(default_factory=list)
    examination_type: list[KnowledgeBaseExaminationTypeCore] = Field(
        default_factory=list
    )
    finding: list[FindingCore] = Field(default_factory=list)
    finding_type: list[FindingTypeCore] = Field(default_factory=list)
    indication: list[IndicationCore] = Field(default_factory=list)
    indication_type: list[IndicationTypeCore] = Field(default_factory=list)
    intervention: list[InterventionCore] = Field(default_factory=list)
    intervention_type: list[InterventionTypeCore] = Field(default_factory=list)
    unit: list[UnitCore] = Field(default_factory=list)
    unit_type: list[UnitTypeCore] = Field(default_factory=list)
    information_source: list[InformationSourceCore] = Field(default_factory=list)
    information_source_type: list[InformationSourceTypeCore] = Field(
        default_factory=list
    )
    citation: list[CitationCore] = Field(default_factory=list)

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_default=True,
        revalidate_instances="always",
    )

    _REFERENCE_FIELDS: ClassVar[dict[str, dict[str, str]]] = {
        "classification": {
            "classification_choices": "classification_choice",
            "classification_types": "classification_type",
        },
        "classification_choice": {
            "classification_choice_descriptors": ("classification_choice_descriptor"),
        },
        "examination": {
            "findings": "finding",
            "examination_types": "examination_type",
            "indications": "indication",
        },
        "finding": {
            "finding_types": "finding_type",
            "classifications": "classification",
            "interventions": "intervention",
            "caused_by_interventions": "intervention",
        },
        "indication": {
            "indication_types": "indication_type",
            "classifications": "classification",
            "interventions": "intervention",
        },
        "intervention": {"intervention_types": "intervention_type"},
        "unit": {"unit_types": "unit_type"},
        "information_source": {"information_source_types": "information_source_type"},
    }
    _OPTIONAL_REFERENCE_FIELDS: ClassVar[dict[str, dict[str, str]]] = {
        "classification_choice_descriptor": {"unit": "unit"},
    }

    @model_validator(mode="after")
    def validate_graph(self) -> Self:
        identity = validate_optional_knowledge_base_identity(
            self.knowledge_base_module,
            self.knowledge_base_version,
        )
        if identity is not None and identity.knowledge_base_module != self.module_name:
            raise ValueError(
                "module_name and knowledge_base_module must identify the same module"
            )

        collection_names: dict[str, set[str]] = {}
        seen_uuids: dict[str, str] = {}

        for field_name in self.__class__.model_fields:
            if field_name in {
                "module_name",
                "knowledge_base_module",
                "knowledge_base_version",
            }:
                continue
            records = getattr(self, field_name)
            names = [record.name for record in records]
            if len(names) != len(set(names)):
                raise ValueError(f"{field_name} names must be unique")
            collection_names[field_name] = set(names)

            for record in records:
                if record.uuid is None:
                    continue
                previous = seen_uuids.get(record.uuid)
                if previous is not None:
                    raise ValueError(
                        f"uuid {record.uuid!r} is shared by {previous} and {field_name}"
                    )
                seen_uuids[record.uuid] = field_name

        for source_name, reference_fields in self._REFERENCE_FIELDS.items():
            for record in getattr(self, source_name):
                for reference_field, target_name in reference_fields.items():
                    references = getattr(record, reference_field)
                    missing = sorted(set(references) - collection_names[target_name])
                    if missing:
                        raise ValueError(
                            f"{source_name}.{record.name}.{reference_field} contains "
                            f"unknown {target_name} names: {', '.join(missing)}"
                        )

        for source_name, reference_fields in self._OPTIONAL_REFERENCE_FIELDS.items():
            for record in getattr(self, source_name):
                for reference_field, target_name in reference_fields.items():
                    reference = getattr(record, reference_field)
                    if (
                        reference is not None
                        and reference not in collection_names[target_name]
                    ):
                        raise ValueError(
                            f"{source_name}.{record.name}.{reference_field} contains "
                            f"unknown {target_name} name: {reference}"
                        )
        return self


def _validate_names(values: list[str], *, field_name: str) -> list[str]:
    if any(not value for value in values):
        raise ValueError(f"{field_name} must not contain empty names")
    if len(values) != len(set(values)):
        raise ValueError(f"{field_name} must contain unique names")
    return values


__all__ = [
    "CitationCore",
    "ClassificationChoiceCore",
    "ClassificationChoiceDescriptorCore",
    "ClassificationCore",
    "ClassificationTypeCore",
    "CoreConceptBase",
    "CoreConceptCollection",
    "ExaminationCore",
    "FindingCore",
    "FindingTypeCore",
    "IndicationCore",
    "IndicationTypeCore",
    "InformationSourceCore",
    "InformationSourceTypeCore",
    "InterventionCore",
    "InterventionTypeCore",
    "KnowledgeBaseExaminationTypeCore",
    "UnitCore",
    "UnitTypeCore",
]
