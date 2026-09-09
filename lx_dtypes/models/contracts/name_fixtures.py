from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class CenterNameFixtureFieldsPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    name: str
    first_names: list[str] = Field(default_factory=list)
    last_names: list[str] = Field(default_factory=list)


class CenterNameFixturePayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    model: str
    fields: CenterNameFixtureFieldsPayload


class NameRecordPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    model: str
    fields: dict[str, str]


__all__ = [
    "CenterNameFixtureFieldsPayload",
    "CenterNameFixturePayload",
    "NameRecordPayload",
]
