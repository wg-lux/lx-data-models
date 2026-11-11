"""Read-only media suggestions and explicit label-to-finding mappings."""

from typing import Literal
from uuid import UUID

from pydantic import Field

from lx_dtypes.models.model import DtypesModel, StrictContractModel

from .knowledge_base import KnowledgeBaseIdentity


class LabelFindingMapping(StrictContractModel):
    label: str = Field(min_length=1)
    modalities: list[Literal["segment", "frame"]]
    finding_name: str = Field(min_length=1)
    intervention_name: str | None = None


class AnnotationFindingMappings(KnowledgeBaseIdentity):
    schema_version: Literal["coloreg_annotation_mapping_v1"]
    labelset_names: list[str]
    mappings: list[LabelFindingMapping]


class FindingSuggestion(DtypesModel):
    id: int = Field(gt=0)
    name: str
    title: str
    source: Literal["report", "prediction"]
    presence: Literal["present", "absent", "uncertain"]
    evidence: list[str]
    instance: UUID
    approved: bool = False


class FindingSuggestions(DtypesModel):
    examination: int | None
    candidates: list[FindingSuggestion] = Field(default_factory=list[FindingSuggestion])
    reason: str = ""
