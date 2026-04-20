from collections.abc import Mapping
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, model_validator

from lx_dtypes.models.knowledge_base.report_template.ValidatorRequirementReferenceDataDict import (
    ValidatorRequirementKindLiteral,
    ValidatorRequirementReferenceDataDict,
)

ValidatorRequirementKind = Literal[
    "classification",
    "finding",
    "intervention",
    "unit",
]


class ValidatorRequirementReference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: ValidatorRequirementKindLiteral
    name: str
    required: bool = True
    finding: str | None = None
    classification: str | None = None

    @model_validator(mode="before")
    @classmethod
    def normalize_legacy_reference_shape(cls, value: Any) -> Any:
        if not isinstance(value, Mapping):
            return value
        data = dict(value)
        if "kind" in data and "name" in data:
            return data
        for legacy_key in ("classification", "finding", "intervention", "unit"):
            legacy_value = data.get(legacy_key)
            if legacy_value in (None, ""):
                continue
            data["kind"] = legacy_key
            data["name"] = str(legacy_value).strip()
            break
        return data

    @model_validator(mode="after")
    def validate_reference_shape(self) -> "ValidatorRequirementReference":
        if not self.name.strip():
            raise ValueError("requirement reference name cannot be empty")
        if self.kind == "unit" and self.classification is None:
            raise ValueError(
                "unit requirement references must declare the target `classification`."
            )
        return self

    @property
    def ddict(self) -> ValidatorRequirementReferenceDataDict:
        data: ValidatorRequirementReferenceDataDict = {
            "kind": self.kind,
            "name": self.name,
            "required": self.required,
        }
        if self.finding is not None:
            data["finding"] = self.finding
        if self.classification is not None:
            data["classification"] = self.classification
        return data
