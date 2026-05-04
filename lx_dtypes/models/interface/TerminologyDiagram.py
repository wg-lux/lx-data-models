from __future__ import annotations

import re
from typing import Any, Literal, Mapping

from pydantic import BaseModel, Field


TerminologyNodeType = Literal[
    "examination",
    "finding",
    "classification",
    "classification_choice",
    "classification_choice_descriptor",
    "intervention",
    "unit",
    "rule",
    "rule_group",
]

TerminologyEdgeType = Literal[
    "examination_to_finding",
    "finding_to_classification",
    "classification_to_choice",
    "choice_to_descriptor",
    "finding_to_intervention",
    "finding_caused_by_intervention",
    "finding_to_rule",
    "classification_to_rule",
    "intervention_to_rule",
    "unit_to_rule",
    "rule_group_to_rule",
    "rule_group_to_rule_group",
    "rule_condition",
    "rule_requires",
]


class TerminologyGraphNode(BaseModel):
    node_id: str
    node_type: TerminologyNodeType
    name: str
    label: str | None = None
    missing: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class TerminologyGraphEdge(BaseModel):
    source_node_id: str
    target_node_id: str
    edge_type: TerminologyEdgeType
    label: str | None = None
    weight: float = 1.0


class TerminologyGraph(BaseModel):
    nodes: list[TerminologyGraphNode] = Field(default_factory=list)
    edges: list[TerminologyGraphEdge] = Field(default_factory=list)

    def as_ddict(self) -> dict[str, Any]:
        return self.model_dump(mode="python")

    def export_mermaid(self) -> str:
        lines = ["flowchart LR"]
        if not self.nodes:
            lines.append('  empty["Keine Terminologieeinträge"]')
            return "\n".join(lines)

        for node in sorted(self.nodes, key=lambda item: (item.node_type, item.name)):
            node_id = _mermaid_id(node.node_id)
            label = node.label or node.name
            lines.append(f'  {node_id}["{_escape_mermaid(label)}"]')

        for edge in sorted(
            self.edges,
            key=lambda item: (
                item.source_node_id,
                item.target_node_id,
                item.edge_type,
                item.label or "",
            ),
        ):
            source_id = _mermaid_id(edge.source_node_id)
            target_id = _mermaid_id(edge.target_node_id)
            label = edge.label or _default_edge_label(edge.edge_type)
            lines.append(
                f"  {source_id} -->|{_escape_mermaid(label)}| {target_id}"
            )

        lines.extend(
            [
                "  classDef missing stroke:#b42318,stroke-dasharray:4 3;",
                "  classDef rule fill:#fff7ed,stroke:#c2410c;",
                "  classDef finding fill:#eff6ff,stroke:#2563eb;",
                "  classDef classification fill:#ecfdf3,stroke:#16a34a;",
            ]
        )
        for node in self.nodes:
            node_id = _mermaid_id(node.node_id)
            if node.missing:
                lines.append(f"  class {node_id} missing;")
            elif node.node_type in {"rule", "rule_group"}:
                lines.append(f"  class {node_id} rule;")
            elif node.node_type == "finding":
                lines.append(f"  class {node_id} finding;")
            elif node.node_type == "classification":
                lines.append(f"  class {node_id} classification;")
        return "\n".join(lines)

    def export_dot(self) -> str:
        lines = ["digraph terminology_graph {"]
        lines.append('  rankdir="LR";')
        for node in sorted(self.nodes, key=lambda item: (item.node_type, item.name)):
            attrs = {
                "label": node.label or node.name,
                "shape": (
                    "box"
                    if node.node_type in {"rule", "rule_group"}
                    else "ellipse"
                ),
            }
            if node.missing:
                attrs["style"] = "dashed"
            lines.append(
                f'  "{_escape_dot(node.node_id)}" '
                f"[{_format_dot_attrs(attrs)}];"
            )

        for edge in sorted(
            self.edges,
            key=lambda item: (
                item.source_node_id,
                item.target_node_id,
                item.edge_type,
                item.label or "",
            ),
        ):
            label = edge.label or _default_edge_label(edge.edge_type)
            lines.append(
                f'  "{_escape_dot(edge.source_node_id)}" -> '
                f'"{_escape_dot(edge.target_node_id)}" [label="{_escape_dot(label)}"];'
            )
        lines.append("}")
        return "\n".join(lines)


class _GraphBuilder:
    def __init__(self) -> None:
        self.nodes: dict[str, TerminologyGraphNode] = {}
        self.edge_keys: set[tuple[str, str, str, str | None]] = set()
        self.edges: list[TerminologyGraphEdge] = []

    def add_node(
        self,
        *,
        node_type: TerminologyNodeType,
        name: str,
        label: str | None = None,
        missing: bool = False,
        metadata: Mapping[str, Any] | None = None,
    ) -> str:
        normalized_name = str(name).strip()
        node_id = f"{node_type}:{normalized_name}"
        existing = self.nodes.get(node_id)
        if existing is None:
            self.nodes[node_id] = TerminologyGraphNode(
                node_id=node_id,
                node_type=node_type,
                name=normalized_name,
                label=label,
                missing=missing,
                metadata=dict(metadata or {}),
            )
        elif existing.missing and not missing:
            existing.missing = False
        return node_id

    def add_edge(
        self,
        *,
        source_node_id: str,
        target_node_id: str,
        edge_type: TerminologyEdgeType,
        label: str | None = None,
        weight: float = 1.0,
    ) -> None:
        key = (source_node_id, target_node_id, edge_type, label)
        if key in self.edge_keys:
            return
        self.edge_keys.add(key)
        self.edges.append(
            TerminologyGraphEdge(
                source_node_id=source_node_id,
                target_node_id=target_node_id,
                edge_type=edge_type,
                label=label,
                weight=weight,
            )
        )

    def build(self) -> TerminologyGraph:
        return TerminologyGraph(nodes=list(self.nodes.values()), edges=self.edges)


def build_terminology_graph(kb: Any) -> TerminologyGraph:
    builder = _GraphBuilder()

    examinations = _registry(kb, "examination")
    findings = _registry(kb, "finding")
    classifications = _registry(kb, "classification")
    choices = _registry(kb, "classification_choice")
    descriptors = _registry(kb, "classification_choice_descriptor")
    interventions = _registry(kb, "intervention")
    units = _registry(kb, "unit")

    for name, record in examinations.items():
        examination_id = builder.add_node(
            node_type="examination",
            name=name,
            label=_node_label("Untersuchung", record, name),
        )
        for finding_name in _as_list(getattr(record, "findings", [])):
            finding_id = _ensure_reference_node(
                builder,
                registry=findings,
                node_type="finding",
                name=finding_name,
                prefix="Befund",
            )
            builder.add_edge(
                source_node_id=examination_id,
                target_node_id=finding_id,
                edge_type="examination_to_finding",
            )

    for name, record in findings.items():
        finding_id = builder.add_node(
            node_type="finding",
            name=name,
            label=_node_label("Befund", record, name),
        )
        for classification_name in _as_list(getattr(record, "classifications", [])):
            classification_id = _ensure_reference_node(
                builder,
                registry=classifications,
                node_type="classification",
                name=classification_name,
                prefix="Klassifikation",
            )
            builder.add_edge(
                source_node_id=finding_id,
                target_node_id=classification_id,
                edge_type="finding_to_classification",
            )

        for intervention_name in _as_list(getattr(record, "interventions", [])):
            intervention_id = _ensure_reference_node(
                builder,
                registry=interventions,
                node_type="intervention",
                name=intervention_name,
                prefix="Intervention",
            )
            builder.add_edge(
                source_node_id=finding_id,
                target_node_id=intervention_id,
                edge_type="finding_to_intervention",
            )

        for intervention_name in _as_list(
            getattr(record, "caused_by_interventions", [])
        ):
            intervention_id = _ensure_reference_node(
                builder,
                registry=interventions,
                node_type="intervention",
                name=intervention_name,
                prefix="Intervention",
            )
            builder.add_edge(
                source_node_id=intervention_id,
                target_node_id=finding_id,
                edge_type="finding_caused_by_intervention",
            )

    for name, record in classifications.items():
        classification_id = builder.add_node(
            node_type="classification",
            name=name,
            label=_node_label("Klassifikation", record, name),
        )
        for choice_name in _as_list(getattr(record, "classification_choices", [])):
            choice_id = _ensure_reference_node(
                builder,
                registry=choices,
                node_type="classification_choice",
                name=choice_name,
                prefix="Auswahlwert",
            )
            builder.add_edge(
                source_node_id=classification_id,
                target_node_id=choice_id,
                edge_type="classification_to_choice",
            )

    for name, record in choices.items():
        choice_id = builder.add_node(
            node_type="classification_choice",
            name=name,
            label=_node_label("Auswahlwert", record, name),
        )
        for descriptor_name in _as_list(
            getattr(record, "classification_choice_descriptors", [])
        ):
            descriptor_id = _ensure_reference_node(
                builder,
                registry=descriptors,
                node_type="classification_choice_descriptor",
                name=descriptor_name,
                prefix="Deskriptor",
            )
            builder.add_edge(
                source_node_id=choice_id,
                target_node_id=descriptor_id,
                edge_type="choice_to_descriptor",
            )

    for name, record in interventions.items():
        builder.add_node(
            node_type="intervention",
            name=name,
            label=_node_label("Intervention", record, name),
        )

    for name, record in units.items():
        builder.add_node(
            node_type="unit",
            name=name,
            label=_node_label("Einheit", record, name),
        )

    _add_findings_validators(builder, kb, findings, classifications)
    _add_classification_validators(builder, kb, findings, classifications)
    _add_intervention_validators(builder, kb, findings, interventions, classifications)
    _add_unit_validators(builder, kb, findings, classifications, units)
    _add_examination_validators(builder, kb)

    return builder.build()


def export_terminology_mermaid(kb: Any) -> str:
    return build_terminology_graph(kb).export_mermaid()


def export_terminology_dot(kb: Any) -> str:
    return build_terminology_graph(kb).export_dot()


def _add_findings_validators(
    builder: _GraphBuilder,
    kb: Any,
    findings: Mapping[str, Any],
    classifications: Mapping[str, Any],
) -> None:
    for name, validator in _registry(kb, "findings_validator").items():
        rule_id = builder.add_node(
            node_type="rule",
            name=f"findings_validator:{name}",
            label=f"Regel: {name}",
            metadata={"rule_kind": "findings_validator"},
        )
        finding_name = str(getattr(validator, "finding", "")).strip()
        if finding_name:
            finding_id = _ensure_reference_node(
                builder,
                registry=findings,
                node_type="finding",
                name=finding_name,
                prefix="Befund",
            )
            builder.add_edge(
                source_node_id=finding_id,
                target_node_id=rule_id,
                edge_type="finding_to_rule",
                label=str(getattr(validator, "operator", "Regel")),
            )
        _add_condition_edges(builder, rule_id, validator, classifications)


def _add_classification_validators(
    builder: _GraphBuilder,
    kb: Any,
    findings: Mapping[str, Any],
    classifications: Mapping[str, Any],
) -> None:
    for name, validator in _registry(kb, "classification_validator").items():
        rule_id = builder.add_node(
            node_type="rule",
            name=f"classification_validator:{name}",
            label=f"Regel: {name}",
            metadata={"rule_kind": "classification_validator"},
        )
        finding_name = str(getattr(validator, "finding", "")).strip()
        classification_name = str(getattr(validator, "classification", "")).strip()
        if finding_name:
            finding_id = _ensure_reference_node(
                builder,
                registry=findings,
                node_type="finding",
                name=finding_name,
                prefix="Befund",
            )
            builder.add_edge(
                source_node_id=finding_id,
                target_node_id=rule_id,
                edge_type="finding_to_rule",
                label="Kontext",
            )
        if classification_name:
            classification_id = _ensure_reference_node(
                builder,
                registry=classifications,
                node_type="classification",
                name=classification_name,
                prefix="Klassifikation",
            )
            builder.add_edge(
                source_node_id=classification_id,
                target_node_id=rule_id,
                edge_type="classification_to_rule",
                label=str(getattr(validator, "operator", "Regel")),
            )
        _add_condition_edges(builder, rule_id, validator, classifications)


def _add_intervention_validators(
    builder: _GraphBuilder,
    kb: Any,
    findings: Mapping[str, Any],
    interventions: Mapping[str, Any],
    classifications: Mapping[str, Any],
) -> None:
    for name, validator in _registry(kb, "intervention_validator").items():
        rule_id = builder.add_node(
            node_type="rule",
            name=f"intervention_validator:{name}",
            label=f"Regel: {name}",
            metadata={"rule_kind": "intervention_validator"},
        )
        finding_name = str(getattr(validator, "finding", "")).strip()
        intervention_name = str(getattr(validator, "intervention", "")).strip()
        if finding_name:
            finding_id = _ensure_reference_node(
                builder,
                registry=findings,
                node_type="finding",
                name=finding_name,
                prefix="Befund",
            )
            builder.add_edge(
                source_node_id=finding_id,
                target_node_id=rule_id,
                edge_type="finding_to_rule",
                label="Kontext",
            )
        if intervention_name:
            intervention_id = _ensure_reference_node(
                builder,
                registry=interventions,
                node_type="intervention",
                name=intervention_name,
                prefix="Intervention",
            )
            builder.add_edge(
                source_node_id=intervention_id,
                target_node_id=rule_id,
                edge_type="intervention_to_rule",
                label=str(getattr(validator, "operator", "Regel")),
            )
        _add_condition_edges(builder, rule_id, validator, classifications)


def _add_unit_validators(
    builder: _GraphBuilder,
    kb: Any,
    findings: Mapping[str, Any],
    classifications: Mapping[str, Any],
    units: Mapping[str, Any],
) -> None:
    for name, validator in _registry(kb, "unit_validator").items():
        rule_id = builder.add_node(
            node_type="rule",
            name=f"unit_validator:{name}",
            label=f"Regel: {name}",
            metadata={"rule_kind": "unit_validator"},
        )
        finding_name = str(getattr(validator, "finding", "")).strip()
        classification_name = str(getattr(validator, "classification", "")).strip()
        unit_name = str(getattr(validator, "unit", "")).strip()
        if finding_name:
            finding_id = _ensure_reference_node(
                builder,
                registry=findings,
                node_type="finding",
                name=finding_name,
                prefix="Befund",
            )
            builder.add_edge(
                source_node_id=finding_id,
                target_node_id=rule_id,
                edge_type="finding_to_rule",
                label="Kontext",
            )
        if classification_name:
            classification_id = _ensure_reference_node(
                builder,
                registry=classifications,
                node_type="classification",
                name=classification_name,
                prefix="Klassifikation",
            )
            builder.add_edge(
                source_node_id=classification_id,
                target_node_id=rule_id,
                edge_type="classification_to_rule",
                label="Klassifikation",
            )
        if unit_name:
            unit_id = _ensure_reference_node(
                builder,
                registry=units,
                node_type="unit",
                name=unit_name,
                prefix="Einheit",
            )
            builder.add_edge(
                source_node_id=unit_id,
                target_node_id=rule_id,
                edge_type="unit_to_rule",
                label=str(getattr(validator, "operator", "Regel")),
            )
        _add_condition_edges(builder, rule_id, validator, classifications)


def _add_examination_validators(builder: _GraphBuilder, kb: Any) -> None:
    finding_validator_names = set(_registry(kb, "findings_validator"))
    examination_validator_names = set(_registry(kb, "examination_validator"))
    for name, validator in _registry(kb, "examination_validator").items():
        group_id = builder.add_node(
            node_type="rule_group",
            name=f"examination_validator:{name}",
            label=f"Regelgruppe: {name}",
            metadata={"rule_kind": "examination_validator"},
        )
        for rule_name in _as_list(getattr(validator, "finding_validators", [])):
            rule_id = builder.add_node(
                node_type="rule",
                name=f"findings_validator:{rule_name}",
                label=f"Regel: {rule_name}",
                missing=rule_name not in finding_validator_names,
                metadata={"rule_kind": "findings_validator"},
            )
            builder.add_edge(
                source_node_id=group_id,
                target_node_id=rule_id,
                edge_type="rule_group_to_rule",
            )
        for group_name in _as_list(getattr(validator, "examination_validators", [])):
            nested_group_id = builder.add_node(
                node_type="rule_group",
                name=f"examination_validator:{group_name}",
                label=f"Regelgruppe: {group_name}",
                missing=group_name not in examination_validator_names,
                metadata={"rule_kind": "examination_validator"},
            )
            builder.add_edge(
                source_node_id=group_id,
                target_node_id=nested_group_id,
                edge_type="rule_group_to_rule_group",
            )


def _add_condition_edges(
    builder: _GraphBuilder,
    rule_id: str,
    validator: Any,
    classifications: Mapping[str, Any],
) -> None:
    query = getattr(validator, "query", None)
    condition = getattr(query, "condition", None)
    if condition is None:
        return

    for branch_name in ("any", "all"):
        for clause in list(getattr(condition, branch_name, []) or []):
            classification_name = str(getattr(clause, "classification", "")).strip()
            if not classification_name:
                continue
            classification_id = _ensure_reference_node(
                builder,
                registry=classifications,
                node_type="classification",
                name=classification_name,
                prefix="Klassifikation",
            )
            comparator = str(getattr(clause, "comparator", "")).strip()
            label = f"Bedingung {branch_name}"
            if comparator:
                label = f"{label}: {comparator}"
            builder.add_edge(
                source_node_id=rule_id,
                target_node_id=classification_id,
                edge_type="rule_condition",
                label=label,
            )

    for requirement in list(getattr(condition, "then_requires", []) or []):
        kind = str(getattr(requirement, "kind", "")).strip()
        name = str(getattr(requirement, "name", "")).strip()
        if not kind or not name:
            continue
        node_type = _requirement_node_type(kind)
        if node_type is None:
            continue
        target_id = builder.add_node(
            node_type=node_type,
            name=name,
            label=f"{_requirement_prefix(kind)}: {name}",
            missing=True,
        )
        builder.add_edge(
            source_node_id=rule_id,
            target_node_id=target_id,
            edge_type="rule_requires",
            label="erfordert",
        )


def _ensure_reference_node(
    builder: _GraphBuilder,
    *,
    registry: Mapping[str, Any],
    node_type: TerminologyNodeType,
    name: str,
    prefix: str,
) -> str:
    record = registry.get(name)
    return builder.add_node(
        node_type=node_type,
        name=name,
        label=_node_label(prefix, record, name),
        missing=record is None,
    )


def _node_label(prefix: str, record: Any, fallback_name: str) -> str:
    if record is None:
        return f"{prefix}: {fallback_name}"
    display_name = (
        str(getattr(record, "name_de", "") or "").strip()
        or str(getattr(record, "name_en", "") or "").strip()
        or str(getattr(record, "name", "") or "").strip()
        or fallback_name
    )
    return f"{prefix}: {display_name}"


def _registry(kb: Any, name: str) -> Mapping[str, Any]:
    value = getattr(kb, name, {})
    if isinstance(value, Mapping):
        return value
    return {}


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        stripped = value.strip()
        return [stripped] if stripped else []
    if isinstance(value, (list, tuple, set)):
        return [str(item).strip() for item in value if str(item).strip()]
    return [str(value).strip()] if str(value).strip() else []


def _requirement_node_type(kind: str) -> TerminologyNodeType | None:
    mapping: dict[str, TerminologyNodeType] = {
        "classification": "classification",
        "finding": "finding",
        "intervention": "intervention",
        "unit": "unit",
    }
    return mapping.get(kind)


def _requirement_prefix(kind: str) -> str:
    return {
        "classification": "Klassifikation",
        "finding": "Befund",
        "intervention": "Intervention",
        "unit": "Einheit",
    }.get(kind, kind)


def _default_edge_label(edge_type: str) -> str:
    return {
        "examination_to_finding": "Befund",
        "finding_to_classification": "Klassifikation",
        "classification_to_choice": "Auswahl",
        "choice_to_descriptor": "Deskriptor",
        "finding_to_intervention": "Intervention",
        "finding_caused_by_intervention": "verursacht",
        "finding_to_rule": "Regel",
        "classification_to_rule": "Regel",
        "intervention_to_rule": "Regel",
        "unit_to_rule": "Regel",
        "rule_group_to_rule": "enthält",
        "rule_group_to_rule_group": "enthält",
        "rule_condition": "Bedingung",
        "rule_requires": "erfordert",
    }.get(edge_type, edge_type)


def _mermaid_id(value: str) -> str:
    slug = re.sub(r"[^0-9A-Za-z_]+", "_", value).strip("_")
    return f"n_{slug or 'node'}"


def _escape_mermaid(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", " ")
        .replace("|", "/")
    )


def _escape_dot(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")


def _format_dot_attrs(attrs: Mapping[str, str]) -> str:
    return ", ".join(
        f'{key}="{_escape_dot(str(value))}"' for key, value in attrs.items()
    )


__all__ = [
    "TerminologyGraph",
    "TerminologyGraphEdge",
    "TerminologyGraphNode",
    "build_terminology_graph",
    "export_terminology_dot",
    "export_terminology_mermaid",
]
