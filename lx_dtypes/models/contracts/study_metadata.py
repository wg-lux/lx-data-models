"""Portable study eligibility metadata; hosts own evaluation and authorization."""

from __future__ import annotations

from typing import Literal, Self, TypedDict

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .deployment_setup import PackageName, PackageVersion
from .finding_extraction import FindingPresence
from .json_types import JsonObject, JsonValue
from .study_analysis import StudyAnalysisDefinition


class StudyMetadataModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, str_strip_whitespace=True)


class ParticipatingCenter(StudyMetadataModel):
    center_key: str = Field(min_length=1, max_length=255)
    name: str = Field(min_length=1, max_length=255)


class StudyAgeGroup(StudyMetadataModel):
    name: str = Field(min_length=1, max_length=255)
    minimum_age: int = Field(ge=0, le=150)
    maximum_age: int | None = Field(default=None, ge=0, le=150)

    @model_validator(mode="after")
    def ordered_bounds(self) -> Self:
        if self.maximum_age is not None and self.maximum_age < self.minimum_age:
            raise ValueError("maximum_age must be at least minimum_age")
        return self


class StudyTerminologyRequirement(StudyMetadataModel):
    module: PackageName
    version: PackageVersion


class StudyConceptReference(StudyTerminologyRequirement):
    kind: Literal["examination", "finding"]
    name: str = Field(min_length=1, max_length=255)


class StudyInclusionCriterion(StudyMetadataModel):
    name: str = Field(min_length=1, max_length=255)
    description: str = Field(default="", max_length=10000)
    concepts: list[StudyConceptReference] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def unique_concepts(self) -> Self:
        keys = [(c.module, c.version, c.kind, c.name) for c in self.concepts]
        if len(keys) != len(set(keys)):
            raise ValueError("criterion concepts must be unique")
        return self


class StudyTextRuleModel(BaseModel):
    # Matcher patterns keep whitespace exactly as authored.
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    module: PackageName
    version: PackageVersion
    finding: str = Field(min_length=1, max_length=255)
    pattern: list[dict[str, JsonValue]] = Field(min_length=1, max_length=100)

    @field_validator("pattern", mode="before")
    @classmethod
    def canonical_pattern_keys(cls, value: object) -> object:
        """Store spaCy keys in upper case so case-converting clients round-trip.

        Browser clients convert keys to camelCase and back to snake_case, which
        turns ``IS_ALPHA`` into ``is_alpha``. Custom ``_`` extension attributes
        carry case-sensitive names and are therefore not supported here.
        """

        def canonical(item: object) -> object:
            if isinstance(item, list):
                return [canonical(entry) for entry in item]
            if isinstance(item, dict):
                keys = [key for key in item if isinstance(key, str)]
                if "_" in keys:
                    raise ValueError("custom extension attributes are not supported")
                upper = [key.upper() for key in keys]
                if len(set(upper)) != len(upper):
                    raise ValueError("pattern keys must be unique ignoring case")
                return {
                    (key.upper() if isinstance(key, str) else key): canonical(entry)
                    for key, entry in item.items()
                }
            return item

        return canonical(value)


class StudyFindingTextRule(StudyTextRuleModel):
    presence: FindingPresence


class StudyClassificationTextRule(StudyTextRuleModel):
    classification: str = Field(min_length=1, max_length=255)
    choice: str = Field(min_length=1, max_length=255)


class StudyMetadata(StudyMetadataModel):
    participating_centers: list[ParticipatingCenter] = Field(
        default_factory=list, max_length=500
    )
    age_groups: list[StudyAgeGroup] = Field(default_factory=list, max_length=100)
    terminology_requirements: list[StudyTerminologyRequirement] = Field(
        default_factory=list, max_length=100
    )
    inclusion_criteria: list[StudyInclusionCriterion] = Field(
        default_factory=list, max_length=100
    )
    analysis_definitions: list[StudyAnalysisDefinition] = Field(
        default_factory=list, max_length=100
    )
    text_extraction: list[StudyFindingTextRule] = Field(
        default_factory=list, max_length=500
    )
    classification_text_extraction: list[StudyClassificationTextRule] = Field(
        default_factory=list, max_length=500
    )

    @model_validator(mode="after")
    def unique_names_and_declared_dependencies(self) -> Self:
        collections = (
            [c.center_key for c in self.participating_centers],
            [g.name for g in self.age_groups],
            [c.name for c in self.inclusion_criteria],
            [(r.module, r.version) for r in self.terminology_requirements],
            [definition.name for definition in self.analysis_definitions],
        )
        for keys in collections:
            if len(keys) != len(set(keys)):
                raise ValueError("study metadata identities must be unique")
        required = {(r.module, r.version) for r in self.terminology_requirements}
        for definition in self.analysis_definitions:
            if (definition.module, definition.version) not in required:
                raise ValueError(
                    "analysis definitions require a declared exact terminology dependency"
                )
        for criterion in self.inclusion_criteria:
            for concept in criterion.concepts:
                if (concept.module, concept.version) not in required:
                    raise ValueError(
                        "inclusion concepts require a declared exact terminology dependency"
                    )
        # The cohort decides what text extraction may suggest: only findings it
        # names as inclusion concepts or analysis units.
        extractable = {
            (concept.module, concept.version, concept.name)
            for criterion in self.inclusion_criteria
            for concept in criterion.concepts
            if concept.kind == "finding"
        }
        extractable.update(
            (definition.module, definition.version, definition.unit_finding)
            for definition in self.analysis_definitions
        )
        for rule in (*self.text_extraction, *self.classification_text_extraction):
            if (rule.module, rule.version, rule.finding) not in extractable:
                raise ValueError(
                    "text extraction rules require a finding declared by the cohort"
                )
        return self


class ParticipatingCenterDataDict(TypedDict):
    center_key: str
    name: str


class StudyAgeGroupDataDict(TypedDict):
    name: str
    minimum_age: int
    maximum_age: int | None


class StudyTerminologyRequirementDataDict(TypedDict):
    module: str
    version: str


class StudyConceptReferenceDataDict(StudyTerminologyRequirementDataDict):
    kind: Literal["examination", "finding"]
    name: str


class StudyInclusionCriterionDataDict(TypedDict):
    name: str
    description: str
    concepts: list[StudyConceptReferenceDataDict]


class StudyFindingTextRuleDataDict(StudyTerminologyRequirementDataDict):
    finding: str
    presence: Literal["present", "absent", "uncertain"]
    pattern: list[JsonObject]


class StudyClassificationTextRuleDataDict(StudyTerminologyRequirementDataDict):
    finding: str
    classification: str
    choice: str
    pattern: list[JsonObject]


class StudyMetadataDataDict(TypedDict):
    participating_centers: list[ParticipatingCenterDataDict]
    age_groups: list[StudyAgeGroupDataDict]
    terminology_requirements: list[StudyTerminologyRequirementDataDict]
    inclusion_criteria: list[StudyInclusionCriterionDataDict]
    analysis_definitions: list[JsonObject]
    text_extraction: list[StudyFindingTextRuleDataDict]
    classification_text_extraction: list[StudyClassificationTextRuleDataDict]
