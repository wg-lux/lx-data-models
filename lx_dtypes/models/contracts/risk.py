from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class RiskNaturalKeyPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    name: str = Field(min_length=1)


class RiskTypeNaturalKeyPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    name: str = Field(min_length=1)


__all__ = ["RiskNaturalKeyPayload", "RiskTypeNaturalKeyPayload"]
