from typing import TypeAlias

ValidationScalar: TypeAlias = str | int | float | bool
ValidationScalarList: TypeAlias = list[ValidationScalar]
ValidationValue: TypeAlias = ValidationScalar | ValidationScalarList
ValidationParams: TypeAlias = dict[str, ValidationValue]
ValidationIssueScalar: TypeAlias = ValidationScalar | None
ValidationIssueValue: TypeAlias = (
    ValidationIssueScalar | list[str] | list[int] | list[float] | list[bool]
)
ValidationIssueDetails: TypeAlias = dict[str, ValidationIssueValue]
