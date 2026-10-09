from __future__ import annotations

from typing import Literal, TypedDict


class ReportTemplateGraphNodeDataDict(TypedDict):
    node_id: str
    node_type: Literal[
        "template",
        "section",
        "finding",
        "classification",
        "validator",
        "patient_field",
        "history_field",
    ]
    name: str
    tokens: list[str]


class ReportTemplateGraphEdgeDataDict(TypedDict):
    source_node_id: str
    target_node_id: str
    edge_type: Literal[
        "template_to_section",
        "section_sequence",
        "section_to_finding",
        "section_to_patient_field",
        "section_to_history_field",
        "finding_to_classification",
        "template_to_validator",
    ]
    weight: float


class ReportTemplateGraphDataDict(TypedDict):
    template_name: str
    examination: str
    start_node_id: str
    ordered_section_node_ids: list[str]
    nodes: list[ReportTemplateGraphNodeDataDict]
    edges: list[ReportTemplateGraphEdgeDataDict]


class ReportTemplateStructureIssueDataDict(TypedDict):
    code: str
    message: str
    level: Literal["error", "warning"]
    node_id: str | None


class ReportTemplateStructureValidationResultDataDict(TypedDict):
    template_name: str
    ok: bool
    graph: ReportTemplateGraphDataDict
    issues: list[ReportTemplateStructureIssueDataDict]
