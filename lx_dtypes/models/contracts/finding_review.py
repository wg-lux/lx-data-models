"""Read-only media suggestions and explicit label-to-finding mappings."""

from typing import Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field
from .knowledge_base import KnowledgeBaseIdentity


class LabelFindingMapping(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    label: str = Field(min_length=1)
    modalities: list[Literal["segment", "frame"]]
    finding_name: str = Field(min_length=1)
    intervention_name: str | None = None


class AnnotationFindingMappings(KnowledgeBaseIdentity):
    schema_version: Literal["coloreg_annotation_mapping_v1"]
    labelset_names: list[str]
    mappings: list[LabelFindingMapping]


class FindingSuggestion(BaseModel):
    id: int = Field(gt=0)
    name: str
    title: str
    source: Literal["report", "prediction"]
    presence: Literal["present", "absent", "uncertain"]
    evidence: list[str]
    instance: UUID
    approved: bool = False


class FindingSuggestions(BaseModel):
    examination: int | None
    candidates: list[FindingSuggestion] = Field(default_factory=list[FindingSuggestion])
    reason: str = ""
