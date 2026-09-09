from __future__ import annotations

from typing import Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, field_validator


@runtime_checkable
class NamedObject(Protocol):
    name: str


def normalize_name_reference(value: str | NamedObject | None, *, default: str) -> str:
    source_value = getattr(value, "name", value)
    normalized = str(source_value or default).strip()
    return normalized or default


class InformationSourceRef(BaseModel):
    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    name: str

    @field_validator("name", mode="before")
    @classmethod
    def normalize(cls, value: str | NamedObject | None) -> str:
        return normalize_name_reference(value, default="manual_annotation")
