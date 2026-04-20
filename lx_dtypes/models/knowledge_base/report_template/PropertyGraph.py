from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class PropertyGraphNode(BaseModel):
    id: str
    kind: str
    labels: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class PropertyGraphEdge(BaseModel):
    source: str
    target: str
    kind: str
    weight: float = 1.0
    properties: dict[str, Any] = Field(default_factory=dict)


class PropertyGraph(BaseModel):
    nodes: dict[str, PropertyGraphNode] = Field(default_factory=dict)
    edges: list[PropertyGraphEdge] = Field(default_factory=list)
