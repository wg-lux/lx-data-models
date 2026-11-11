from __future__ import annotations

from typing import Any

from pydantic import Field

from lx_dtypes.models.model import DtypesModel


class PropertyGraphNode(DtypesModel):
    id: str
    kind: str
    labels: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class PropertyGraphEdge(DtypesModel):
    source: str
    target: str
    kind: str
    weight: float = 1.0
    properties: dict[str, Any] = Field(default_factory=dict)


class PropertyGraph(DtypesModel):
    nodes: dict[str, PropertyGraphNode] = Field(default_factory=dict)
    edges: list[PropertyGraphEdge] = Field(default_factory=list)
