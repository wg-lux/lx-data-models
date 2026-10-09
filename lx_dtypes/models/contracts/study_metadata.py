"""Portable study eligibility metadata; hosts own evaluation and authorization."""

from __future__ import annotations

from typing import Literal, Self, TypedDict

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .deployment_setup import PackageName, PackageVersion


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

    @model_validator(mode="after")
    def unique_names_and_declared_dependencies(self) -> Self:
        collections = (
            [c.center_key for c in self.participating_centers],
            [g.name for g in self.age_groups],
            [c.name for c in self.inclusion_criteria],
            [(r.module, r.version) for r in self.terminology_requirements],
        )
        for keys in collections:
            if len(keys) != len(set(keys)):
                raise ValueError("study metadata identities must be unique")
        required = {(r.module, r.version) for r in self.terminology_requirements}
        for criterion in self.inclusion_criteria:
            for concept in criterion.concepts:
                if (concept.module, concept.version) not in required:
                    raise ValueError(
                        "inclusion concepts require a declared exact terminology dependency"
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


class StudyMetadataDataDict(TypedDict):
    participating_centers: list[ParticipatingCenterDataDict]
    age_groups: list[StudyAgeGroupDataDict]
    terminology_requirements: list[StudyTerminologyRequirementDataDict]
    inclusion_criteria: list[StudyInclusionCriterionDataDict]
