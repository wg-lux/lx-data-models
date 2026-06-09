from collections.abc import Mapping
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from lx_dtypes.models.knowledge_base.report_template.ValidatorRequirementReferenceDataDict import (
    ValidatorRequirementKindLiteral,
    ValidatorRequirementReferenceDataDict,
)

ValidatorRequirementKind = Literal[
    "classification",
    "classification_choice",
    "finding",
    "intervention",
    "unit",
]


class ValidatorRequirementReference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: ValidatorRequirementKindLiteral
    name: str = ""
    names: list[str] = Field(default_factory=list)
    required: bool = True
    finding: str | None = None
    classification: str | None = None

    @model_validator(mode="before")
    @classmethod
    def normalize_legacy_reference_shape(cls, value: Any) -> Any:
        if not isinstance(value, Mapping):
            return value
        data = dict(value)
        raw_names = data.get("names")
        if isinstance(raw_names, list):
            data["names"] = [
                str(item).strip() for item in raw_names if str(item).strip()
            ]
            if not data.get("name") and data["names"]:
                data["name"] = data["names"][0]
        if "kind" in data and "name" in data:
            return data
        for legacy_key in (
            "classification",
            "classification_choice",
            "finding",
            "intervention",
            "unit",
        ):
            legacy_value = data.get(legacy_key)
            if legacy_value in (None, ""):
                continue
            data["kind"] = legacy_key
            data["name"] = str(legacy_value).strip()
            break
        return data

    @model_validator(mode="after")
    def validate_reference_shape(self) -> "ValidatorRequirementReference":
        self.name = self.name.strip()
        self.names = list(
            dict.fromkeys(name.strip() for name in self.names if name.strip())
        )
        if self.names and not self.name:
            self.name = self.names[0]
        if self.name and self.names and self.name not in self.names:
            self.names.insert(0, self.name)
        if not self.name:
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
        if self.names:
            data["names"] = self.names
        if self.finding is not None:
            data["finding"] = self.finding
        if self.classification is not None:
            data["classification"] = self.classification
        return data
