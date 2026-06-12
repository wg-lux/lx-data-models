from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ExaminationTypeCore(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    name: str


__all__ = ["ExaminationTypeCore"]
