from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ContraindicationCore(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    name: str
    description: str | None = None


__all__ = ["ContraindicationCore"]
