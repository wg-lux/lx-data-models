from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ActiveLearningSelectionPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    selection_strategy: str = Field(min_length=1)
    candidate_count: int = Field(ge=0)
    selected_count: int = Field(ge=0)
    annotation_budget: int = Field(ge=0)
    ai_dataset_id: int = Field(ge=1)
    model_meta_id: int = Field(ge=1)
    campaign: str = ""


class ActiveLearningSidecarPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    existing: str = ""
    active_learning: ActiveLearningSelectionPayload


class ActiveLearningSelectionProvenancePayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    ingest_variant: Literal["active_learning_selection"]
    custom_marker: Literal["active_learning"]
    sidecar_payload: ActiveLearningSidecarPayload


__all__ = [
    "ActiveLearningSelectionPayload",
    "ActiveLearningSelectionProvenancePayload",
    "ActiveLearningSidecarPayload",
]
