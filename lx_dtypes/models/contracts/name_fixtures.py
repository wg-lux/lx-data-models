from __future__ import annotations

from pydantic import Field

from lx_dtypes.models.model import FrozenContractModel


class CenterNameFixtureFieldsPayload(FrozenContractModel):
    name: str
    first_names: list[str] = Field(default_factory=list)
    last_names: list[str] = Field(default_factory=list)


class CenterNameFixturePayload(FrozenContractModel):
    model: str
    fields: CenterNameFixtureFieldsPayload


class NameRecordPayload(FrozenContractModel):
    model: str
    fields: dict[str, str]


__all__ = [
    "CenterNameFixtureFieldsPayload",
    "CenterNameFixturePayload",
    "NameRecordPayload",
]
