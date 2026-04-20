from typing import Literal, TypedDict

ValidatorRequirementKindLiteral = Literal[
    "classification",
    "finding",
    "intervention",
    "unit",
]


class ValidatorRequirementReferenceDataDict(TypedDict, total=False):
    kind: ValidatorRequirementKindLiteral
    name: str
    required: bool
    finding: str
    classification: str
