from __future__ import annotations
from pydantic import BaseModel, ConfigDict, Field

# Common configuration shared across your core DTOs
# Keeps data immutable, strict, and prevents unexpected fields
core_config = ConfigDict(extra="forbid", frozen=True, strict=True, from_attributes=True)


class EventCore(BaseModel):
    model_config = core_config

    name: str
    description: str | None = None


class EventClassificationCore(BaseModel):
    model_config = core_config

    name: str
    event_name: str  # Matches your Django natural key approach


class EventClassificationChoiceCore(BaseModel):
    model_config = core_config

    name: str
    event_classification_name: str
    # Typed dicts slightly better by specifying keys are strings
    subcategories: dict[str, object] = Field(default_factory=dict)
    numerical_descriptors: dict[str, object] = Field(default_factory=dict)


class EventClassificationDeep(EventClassificationCore):
    """Includes all choices nested under the classification."""

    choices: list[EventClassificationChoiceCore] = Field(default_factory=list)


class EventDeep(EventCore):
    """Includes all classifications nested under the event."""

    classifications: list[EventClassificationDeep] = Field(default_factory=list)


__all__ = [
    "EventCore",
    "EventClassificationCore",
    "EventClassificationChoiceCore",
    "EventClassificationDeep",
    "EventDeep",
]
