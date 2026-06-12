from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class NameFieldsPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    first_names: list[str] = Field(default_factory=list)
    last_names: list[str] = Field(default_factory=list)


class NameEntryPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    model: str
    fields: NameFieldsPayload


__all__ = ["NameEntryPayload", "NameFieldsPayload"]
