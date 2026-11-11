from __future__ import annotations

from pydantic import ConfigDict, Field

from lx_dtypes.models.contracts.json_types import JsonValue
from lx_dtypes.models.model import FrozenContractModel

# Common configuration shared across your core DTOs
# Keeps data immutable, strict, and prevents unexpected fields
core_config = ConfigDict(from_attributes=True)


class EventCore(FrozenContractModel):
    model_config = core_config

    name: str
    description: str | None = None


class EventClassificationCore(FrozenContractModel):
    model_config = core_config

    name: str
    event_name: str  # Matches your Django natural key approach


class EventClassificationChoiceCore(FrozenContractModel):
    model_config = core_config

    name: str
    event_classification_name: str
    # Typed dicts slightly better by specifying keys are strings
    subcategories: dict[str, JsonValue] = Field(default_factory=dict)
    numerical_descriptors: dict[str, JsonValue] = Field(default_factory=dict)


class EventClassificationDeep(EventClassificationCore):
    """Includes all choices nested under the classification."""

    choices: list[EventClassificationChoiceCore] = Field(default_factory=list)


class EventDeep(EventCore):
    """Includes all classifications nested under the event."""

    classifications: list[EventClassificationDeep] = Field(default_factory=list)


__all__ = [
    "EventClassificationChoiceCore",
    "EventClassificationCore",
    "EventClassificationDeep",
    "EventCore",
    "EventDeep",
]
