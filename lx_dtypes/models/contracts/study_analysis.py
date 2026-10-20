"""Portable, bounded descriptive study rules. No executable expressions or SQL."""

from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .deployment_setup import PackageName, PackageVersion

StudyRole = Literal["index", "polyp", "previous_follow_up", "follow_up"]
StudyScalar = str | float | bool


class StudyAnalysisModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False)


class StudyPredicate(StudyAnalysisModel):
    role: StudyRole = "index"
    classification: str = Field(min_length=1, max_length=255)
    descriptor: str | None = Field(default=None, min_length=1, max_length=255)
    operator: Literal["eq", "ne", "ge", "gt", "le", "lt", "in", "present"]
    value: StudyScalar | list[str] | None = None

    @model_validator(mode="after")
    def operand_shape(self) -> Self:
        if self.operator == "present":
            if self.value is not None:
                raise ValueError("present has no value operand")
        elif self.operator == "in":
            if (
                not isinstance(self.value, list)
                or not self.value
                or len(self.value) > 100
            ):
                raise ValueError("in requires 1–100 string values")
        elif self.operator in {"ge", "gt", "le", "lt"}:
            if self.descriptor is None or not isinstance(self.value, float):
                raise ValueError(
                    "numeric comparisons require a descriptor and numeric value"
                )
        elif self.value is None or isinstance(self.value, list):
            raise ValueError("eq/ne require a scalar value")
        if (
            self.descriptor is None
            and self.operator != "present"
            and not isinstance(self.value, (str, list))
        ):
            raise ValueError("classification choices must be string names")
        return self


class StudyRule(StudyAnalysisModel):
    mode: Literal["all", "any"] = "all"
    predicates: list[StudyPredicate] = Field(min_length=1, max_length=100)


class StudyAnalysisGroup(StudyAnalysisModel):
    name: str = Field(min_length=1, max_length=255)
    rule: StudyRule


class StudyAnalysisEndpoint(StudyAnalysisModel):
    name: str = Field(min_length=1, max_length=255)
    positive: StudyRule
    negative: StudyRule
    eligible: StudyRule | None = None


class StudyAnalysisDefinition(StudyAnalysisModel):
    schema_version: Literal["1"] = "1"
    name: str = Field(min_length=1, max_length=255)
    module: PackageName
    version: PackageVersion
    unit_finding: str = Field(min_length=1, max_length=255)
    status: Literal["draft", "ready"] = "draft"
    unresolved_requirements: list[str] = Field(default_factory=list, max_length=100)
    inclusion: StudyRule | None = None
    groups: list[StudyAnalysisGroup] = Field(min_length=1, max_length=30)
    endpoints: list[StudyAnalysisEndpoint] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def distinct_names(self) -> Self:
        for values in (self.groups, self.endpoints):
            if len({value.name for value in values}) != len(values):
                raise ValueError("group and endpoint names must be unique")
        if self.status == "ready" and self.unresolved_requirements:
            raise ValueError("ready analyses cannot have unresolved requirements")
        return self


class StudyFindingReference(StudyAnalysisModel):
    record_uuid: str = Field(min_length=1)
    finding_uuid: str = Field(min_length=1)


class StudyAnalysisUnit(StudyAnalysisModel):
    """Host-authorized references, assembled with verified lesion linkage."""

    index: StudyFindingReference
    polyp: StudyFindingReference | None = None
    previous_follow_up: StudyFindingReference | None = None
    follow_up: StudyFindingReference | None = None


class StudyEndpointStatistics(StudyAnalysisModel):
    group: str
    endpoint: str
    numerator: int = Field(ge=0)
    denominator: int = Field(ge=0)
    negative: int = Field(ge=0)
    missing: int = Field(ge=0)
    ineligible: int = Field(ge=0)
    eligibility_unknown: int = Field(ge=0)
    conflicting: int = Field(ge=0)
    rate: float | None = None


class StudyDatasetStatistics(StudyAnalysisModel):
    schema_version: Literal["1"] = "1"
    analysis_name: str
    analysis_digest: str
    module: str
    version: str
    method: Literal["descriptive_binary_rates"] = "descriptive_binary_rates"
    total_records: int
    total_units: int
    included_units: int
    excluded_units: int
    inclusion_unknown: int
    unassigned_units: int
    ambiguous_units: int
    endpoints: list[StudyEndpointStatistics]
