from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ExaminationTimeCore(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    name: str


class ExaminationTimeTypeCore(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    name: str


__all__ = ["ExaminationTimeCore", "ExaminationTimeTypeCore"]
