type ValidationScalar = str | int | float | bool
type ValidationScalarList = list[ValidationScalar]
type ValidationValue = ValidationScalar | ValidationScalarList
type ValidationParams = dict[str, ValidationValue]
type ValidationIssueScalar = ValidationScalar | None
type ValidationIssueValue = (
    ValidationIssueScalar | list[str] | list[int] | list[float] | list[bool]
)
type ValidationIssueDetails = dict[str, ValidationIssueValue]
