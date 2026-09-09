from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class FindingInterventionCore(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    name: str
    description: str | None = None


class FindingInterventionTypeCore(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    name: str
    description: str | None = None


__all__ = ["FindingInterventionCore", "FindingInterventionTypeCore"]
