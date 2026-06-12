from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class EventCore(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    name: str
    description: str | None = None


class EventClassificationCore(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    name: str
    event_name: str


class EventClassificationChoiceCore(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    name: str
    event_classification_name: str
    subcategories: dict[str, object] = Field(default_factory=dict)
    numerical_descriptors: dict[str, object] = Field(default_factory=dict)


__all__ = [
    "EventCore",
    "EventClassificationCore",
    "EventClassificationChoiceCore",
]
