from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class DirectVideoPathFileInfo(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    absolute_path: str
    relative_path: str
    size_mb: float = Field(ge=0)


__all__ = ["DirectVideoPathFileInfo"]
