"""Portable, bounded study rules and statistical configuration. No executable expressions or SQL."""

from typing import Literal, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    SerializerFunctionWrapHandler,
    model_serializer,
    model_validator,
)

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


class StudyNumericVariable(StudyAnalysisModel):
    name: str = Field(min_length=1, max_length=255)
    role: StudyRole = "index"
    classification: str = Field(min_length=1, max_length=255)
    descriptor: str = Field(min_length=1, max_length=255)


class StudyInference(StudyAnalysisModel):
    name: str = Field(min_length=1, max_length=255)
    method: Literal["welch_t_test", "paired_t_test", "linear_regression"]
    outcome: str = Field(min_length=1)
    predictors: list[str] = Field(default_factory=list, max_length=20)
    paired_variable: str | None = None
    groups: list[str] = Field(default_factory=list, max_length=2)
    alpha: float = Field(default=0.05, gt=0, lt=1)
    missing: Literal["error", "complete_case"] = "error"

    @model_validator(mode="after")
    def method_fields(self) -> Self:
        if self.method == "welch_t_test":
            if len(set(self.groups)) != 2 or self.predictors or self.paired_variable:
                raise ValueError(
                    "Welch requires two distinct groups and no predictors or pair"
                )
        elif self.method == "paired_t_test":
            if (
                not self.paired_variable
                or self.paired_variable == self.outcome
                or self.predictors
                or self.groups
            ):
                raise ValueError(
                    "paired test requires a distinct paired variable and no groups or predictors"
                )
        elif not self.predictors or self.paired_variable or self.groups:
            raise ValueError("regression requires predictors and no pair or groups")
        if (
            len(set(self.predictors)) != len(self.predictors)
            or self.outcome in self.predictors
        ):
            raise ValueError("predictors must be distinct and exclude the outcome")
        return self


class StudyEstimate(StudyAnalysisModel):
    term: str
    estimate: float
    standard_error: float = Field(gt=0)
    statistic: float
    p_value: float = Field(ge=0, le=1)
    confidence_low: float
    confidence_high: float


class StudyGroupCount(StudyAnalysisModel):
    group: str
    count: int = Field(ge=0)


class StudyInferenceResult(StudyAnalysisModel):
    name: str
    method: Literal["welch_t_test", "paired_t_test", "linear_regression"]
    alpha: float
    alternative: Literal["two-sided"] = "two-sided"
    p_value_adjustment: Literal["none"] = "none"
    observations: int = Field(ge=0)
    missing_observations: int = Field(ge=0)
    group_counts: list[StudyGroupCount] = Field(default_factory=list)
    degrees_of_freedom: float = Field(gt=0)
    r_squared: float | None = None
    estimates: list[StudyEstimate]


PlotState = Literal[
    "positive",
    "negative",
    "missing",
    "conflicting",
    "ineligible",
    "eligibility_unknown",
]


class StudyPlotLabel(StudyAnalysisModel):
    name: str = Field(min_length=1, max_length=255)
    source: Literal["endpoint", "image_annotation", "video_annotation"]
    reference: str = Field(min_length=1, max_length=255)


class StudyPlotConfiguration(StudyAnalysisModel):
    labels: list[StudyPlotLabel] = Field(min_length=1, max_length=50)
    limit: int = Field(default=1000, ge=1, le=5000)

    @model_validator(mode="after")
    def unique_labels(self) -> Self:
        if len({label.name for label in self.labels}) != len(self.labels):
            raise ValueError("plot label names must be unique")
        return self


class StudyPlotValue(StudyAnalysisModel):
    name: str
    value: float | None


class StudyPlotState(StudyAnalysisModel):
    name: str
    state: PlotState


class StudyPlotPoint(StudyAnalysisModel):
    group: str
    values: list[StudyPlotValue]
    labels: list[StudyPlotState]


class StudyPlotRate(StudyAnalysisModel):
    group: str
    label: str
    positive: int
    negative: int
    unknown: int
    rate: float | None
    low: float | None
    high: float | None


class StudyPlotResult(StudyAnalysisModel):
    labels: list[StudyPlotLabel]
    variables: list[str]
    points: list[StudyPlotPoint]
    total: int
    omitted: int
    independent: bool
    confidence: float = 0.95
    rates: list[StudyPlotRate]


class StudyCategorical(StudyAnalysisModel):
    name: str = Field(min_length=1, max_length=255)
    method: Literal["fisher_exact", "chi_square", "diagnostic_accuracy"]
    endpoint: str = Field(min_length=1, max_length=255)
    reference: str | None = None
    groups: list[str] = Field(default_factory=list, max_length=2)
    design: Literal["cohort", "case_control"] | None = None
    alpha: float = Field(default=0.05, gt=0, lt=1)
    missing: Literal["error", "complete_case"] = "error"

    @model_validator(mode="after")
    def method_fields(self) -> Self:
        if self.method == "diagnostic_accuracy":
            if (
                not self.reference
                or self.reference == self.endpoint
                or self.groups
                or self.design
            ):
                raise ValueError(
                    "diagnostic accuracy requires a distinct reference endpoint and no groups or design"
                )
        elif (
            len(set(self.groups)) != 2
            or self.reference is not None
            or self.design is None
        ):
            raise ValueError(
                "categorical comparison requires two distinct groups, study design and no reference"
            )
        return self


class StudyCategoricalEstimate(StudyAnalysisModel):
    term: str
    value: float | None
    low: float | None
    high: float | None
    interval: Literal["conditional_exact", "katz_log", "wilson"]
    note: str = ""


class StudyCategoricalResult(StudyAnalysisModel):
    name: str
    method: Literal["fisher_exact", "chi_square", "diagnostic_accuracy"]
    design: Literal["cohort", "case_control"] | None
    endpoint: str
    reference: str | None
    alpha: float
    observations: int = Field(ge=0)
    excluded: int = Field(ge=0)
    rows: list[str]
    columns: list[str]
    table: list[list[int]]
    statistic: float | None = None
    p: float | None = Field(default=None, ge=0, le=1)
    df: int | None = None
    estimates: list[StudyCategoricalEstimate]


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
    endpoints: list[StudyAnalysisEndpoint] = Field(default_factory=list, max_length=100)
    variables: list[StudyNumericVariable] = Field(default_factory=list, max_length=100)
    inference: list[StudyInference] = Field(default_factory=list, max_length=30)
    categorical: list[StudyCategorical] = Field(default_factory=list, max_length=30)
    plots: StudyPlotConfiguration | None = None

    @model_serializer(mode="wrap")
    def preserve_descriptive_identity(
        self, handler: SerializerFunctionWrapHandler
    ) -> dict[str, object]:
        payload: dict[str, object] = handler(self)
        for name in ("variables", "inference", "categorical"):
            if payload.get(name) == []:
                payload.pop(name)
        if payload.get("plots") is None:
            payload.pop("plots", None)
        return payload

    @model_validator(mode="after")
    def distinct_names(self) -> Self:
        for values in (
            self.groups,
            self.endpoints,
            self.variables,
            self.inference,
            self.categorical,
        ):
            if len({value.name for value in values}) != len(values):
                raise ValueError("group and endpoint names must be unique")
        if self.plots:
            for label in self.plots.labels:
                if label.source == "endpoint" and label.reference not in {
                    endpoint.name for endpoint in self.endpoints
                }:
                    raise ValueError("plot label references an unknown endpoint")
        if not self.endpoints and not self.inference and not self.plots:
            raise ValueError("analysis requires endpoints or inference")
        endpoint_names = {endpoint.name for endpoint in self.endpoints}
        for comparison in self.categorical:
            if comparison.endpoint not in endpoint_names or (
                comparison.reference is not None
                and comparison.reference not in endpoint_names
            ):
                raise ValueError("categorical analysis references an unknown endpoint")
            if not set(comparison.groups) <= {group.name for group in self.groups}:
                raise ValueError("categorical analysis references an unknown group")
        names = {variable.name for variable in self.variables}
        for analysis in self.inference:
            referenced = {analysis.outcome, *analysis.predictors}
            if analysis.paired_variable:
                referenced.add(analysis.paired_variable)
            if not referenced <= names:
                raise ValueError("inference references an unknown numeric variable")
            if not set(analysis.groups) <= {group.name for group in self.groups}:
                raise ValueError("inference references an unknown group")
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
    inference: list[StudyInferenceResult] = Field(default_factory=list)
    categorical: list[StudyCategoricalResult] = Field(default_factory=list)
    plots: StudyPlotResult | None = None
