from typing import Literal, TypedDict

ValidatorRequirementKindLiteral = Literal[
    "classification",
    "classification_choice",
    "finding",
    "intervention",
    "unit",
]


class ValidatorRequirementReferenceDataDict(TypedDict, total=False):
    kind: ValidatorRequirementKindLiteral
    name: str
    names: list[str]
    required: bool
    finding: str
    classification: str
