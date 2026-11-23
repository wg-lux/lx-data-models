"""Graph representation and structural validation of report templates.

A template is projected into a directed graph of sections, findings,
classifications, data fields, and validators. Structural validation walks this
graph to report missing or inconsistent references before a template is used.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import TYPE_CHECKING, Any, Literal, cast

from pydantic import Field

from lx_dtypes.language import DEFAULT_LANGUAGE, LanguageCode, validate_language
from lx_dtypes.models.model import DtypesModel

from .PropertyGraph import PropertyGraph, PropertyGraphEdge, PropertyGraphNode
from .ReportTemplate import ReportTemplate
from .ReportTemplateGraphDataDict import (
    ReportTemplateGraphDataDict,
    ReportTemplateGraphEdgeDataDict,
    ReportTemplateGraphNodeDataDict,
    ReportTemplateStructureIssueDataDict,
    ReportTemplateStructureValidationResultDataDict,
)

if TYPE_CHECKING:
    from .ReportTemplateSection import ReportTemplateSection


_PATIENT_DATA_FIELD_KEYS = {
    # Shipped STAR and DGVS context fields are resolved by the host through
    # each field's declared patient / patient_examination source.
    "name",
    "date_of_birth",
    "examination_date",
    "examiner",
    "assisting_personnel",
    "device_identification",
    "relevant_images",
    "patient_birth_date",
    "patient_gender",
    "patient_age",
    "patient_identifier",
    "patient_id",
    "center",
    "indication",
}

_HISTORY_FIELD_KEYS = {
    "previous_examinations",
    "previous_examination_count",
    "prior_findings_summary",
    "previous_interventions",
    "previous_histology_summary",
}


def _tokenize(text: str | None) -> list[str]:
    if not text:
        return []
    normalized = text.replace("-", " ").replace("_", " ").lower()
    return [part for part in normalized.split() if part]


class ReportTemplateGraphNode(DtypesModel):
    """Node in a report template graph.

    Attributes:
        node_id: Unique identifier of the form ``"<node_type>:<name>"``.
        node_type: Kind of template element the node represents.
        name: Element name.
        tokens: Lowercase search tokens derived from the element's labels.
    """

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
    tokens: list[str] = Field(default_factory=list)

    def as_ddict(self) -> ReportTemplateGraphNodeDataDict:
        """Return the node as a typed dictionary."""
        return cast(ReportTemplateGraphNodeDataDict, self.model_dump(mode="python"))


class ReportTemplateGraphEdge(DtypesModel):
    """Directed, weighted edge between two report template graph nodes."""

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
    weight: float = 1.0

    def as_ddict(self) -> ReportTemplateGraphEdgeDataDict:
        """Return the edge as a typed dictionary."""
        return cast(ReportTemplateGraphEdgeDataDict, self.model_dump(mode="python"))


class ReportTemplateGraph(DtypesModel):
    """Directed graph of a report template and its referenced elements.

    Attributes:
        template_name: Name of the template.
        examination: Examination the template reports on.
        start_node_id: First section node, or the template node if there are
            no sections.
        ordered_section_node_ids: Section nodes in report order.
        nodes: All graph nodes.
        edges: All graph edges.
    """

    template_name: str
    examination: str
    start_node_id: str
    ordered_section_node_ids: list[str] = Field(default_factory=list)
    nodes: list[ReportTemplateGraphNode] = Field(default_factory=list)
    edges: list[ReportTemplateGraphEdge] = Field(default_factory=list)

    def as_ddict(self) -> ReportTemplateGraphDataDict:
        """Return the graph as a typed dictionary."""
        return cast(ReportTemplateGraphDataDict, self.model_dump(mode="python"))


class ReportTemplateStructureIssue(DtypesModel):
    """Problem found while validating a template's structure.

    Attributes:
        code: Stable machine-readable issue code.
        message: Localized description.
        level: ``"error"`` blocks use of the template; ``"warning"`` does not.
        node_id: Graph node the issue refers to, if any.
    """

    code: str
    message: str
    level: Literal["error", "warning"] = "error"
    node_id: str | None = None

    def as_ddict(self) -> ReportTemplateStructureIssueDataDict:
        """Return the issue as a typed dictionary."""
        return cast(
            ReportTemplateStructureIssueDataDict, self.model_dump(mode="python")
        )


class ReportTemplateStructureValidationResult(DtypesModel):
    """Outcome of structural validation for one report template.

    ``ok`` is ``False`` when at least one issue has level ``"error"``.
    """

    template_name: str
    ok: bool
    graph: ReportTemplateGraph
    issues: list[ReportTemplateStructureIssue] = Field(default_factory=list)

    def as_ddict(self) -> ReportTemplateStructureValidationResultDataDict:
        """Return the result as a typed dictionary."""
        return cast(
            ReportTemplateStructureValidationResultDataDict,
            self.model_dump(mode="python"),
        )


def _add_node(
    nodes_by_id: dict[str, ReportTemplateGraphNode],
    *,
    node_id: str,
    node_type: Literal[
        "template",
        "section",
        "finding",
        "classification",
        "validator",
        "patient_field",
        "history_field",
    ],
    name: str,
    token_source: list[str],
) -> None:
    tokens = sorted(set(token_source))
    nodes_by_id.setdefault(
        node_id,
        ReportTemplateGraphNode(
            node_id=node_id,
            node_type=node_type,
            name=name,
            tokens=tokens,
        ),
    )


class ReportTemplatePropertyGraphAdapter:
    def __init__(self, *, tokenizers: list[Any] | None = None) -> None:
        self._tokenizers = tokenizers or [_tokenize]

    def _tokens(self, *parts: str | None) -> list[str]:
        return sorted(
            {
                token
                for part in parts
                for tokenizer in self._tokenizers
                for token in tokenizer(part)
            }
        )

    def _add_property_node(
        self,
        graph: PropertyGraph,
        *,
        node_id: str,
        kind: str,
        name: str,
        token_parts: list[str | None],
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        graph.nodes.setdefault(
            node_id,
            PropertyGraphNode(
                id=node_id,
                kind=kind,
                labels=self._tokens(*token_parts),
                metadata={"name": name, **(dict(metadata or {}))},
            ),
        )

    def _add_property_edge(
        self,
        graph: PropertyGraph,
        *,
        source: str,
        target: str,
        kind: str,
        weight: float = 1.0,
        properties: Mapping[str, Any] | None = None,
    ) -> None:
        graph.edges.append(
            PropertyGraphEdge(
                source=source,
                target=target,
                kind=kind,
                weight=weight,
                properties=dict(properties or {}),
            )
        )

    def build(
        self,
        template: ReportTemplate,
        *,
        sections: Mapping[str, ReportTemplateSection] | Mapping[str, Any],
        report_findings: Mapping[str, Any],
    ) -> PropertyGraph:
        graph = PropertyGraph()
        template_node_id = f"template:{template.name}"
        self._add_property_node(
            graph,
            node_id=template_node_id,
            kind="template",
            name=template.name,
            token_parts=[
                template.name,
                template.examination,
                *template.validators.examination_validators,
                *template.validators.findings_validators,
                *template.validators.classification_validators,
                *template.validators.intervention_validators,
                *template.validators.unit_validators,
            ],
            metadata={"examination": template.examination},
        )

        prev_section_node_id: str | None = None
        for index, section_name in enumerate(template.report_sections):
            section = sections.get(section_name)
            if section is None:
                continue

            section_node_id = f"section:{section_name}"
            self._add_property_node(
                graph,
                node_id=section_node_id,
                kind="section",
                name=section_name,
                token_parts=[
                    section_name,
                    *list(getattr(section, "types", []) or []),
                    str(getattr(section, "section_kind", "findings")),
                    *[
                        str(getattr(field, "key", ""))
                        for field in _section_fields(section)
                    ],
                ],
                metadata={
                    "position": index,
                    "section_kind": str(getattr(section, "section_kind", "findings")),
                },
            )
            self._add_property_edge(
                graph,
                source=template_node_id,
                target=section_node_id,
                kind="template_to_section",
            )

            if prev_section_node_id is not None:
                self._add_property_edge(
                    graph,
                    source=prev_section_node_id,
                    target=section_node_id,
                    kind="section_sequence",
                )
            prev_section_node_id = section_node_id

            section_kind = str(getattr(section, "section_kind", "findings"))
            field_refs = _section_fields(section)
            section_field_weight = 1.0 / max(1.0, float(len(field_refs)))
            for field in field_refs:
                field_key = str(getattr(field, "key", ""))
                if not field_key:
                    continue

                if section_kind in {"patient_data", "medications"}:
                    field_kind = "patient_field"
                    edge_kind = "section_to_patient_field"
                elif section_kind == "history":
                    field_kind = "history_field"
                    edge_kind = "section_to_history_field"
                else:
                    continue

                field_node_id = f"{field_kind}:{field_key}"
                self._add_property_node(
                    graph,
                    node_id=field_node_id,
                    kind=field_kind,
                    name=field_key,
                    token_parts=[field_key],
                )
                self._add_property_edge(
                    graph,
                    source=section_node_id,
                    target=field_node_id,
                    kind=edge_kind,
                    weight=section_field_weight,
                )

            finding_refs = list(section.findings or [])
            section_finding_weight = 1.0 / max(1.0, float(len(finding_refs)))
            for finding_ref in finding_refs:
                finding_name, class_names = _parse_section_finding_ref(
                    finding_ref=finding_ref,
                    report_findings=report_findings,
                )
                if not finding_name:
                    continue

                finding_node_id = f"finding:{finding_name}"
                self._add_property_node(
                    graph,
                    node_id=finding_node_id,
                    kind="finding",
                    name=finding_name,
                    token_parts=[finding_name],
                )
                self._add_property_edge(
                    graph,
                    source=section_node_id,
                    target=finding_node_id,
                    kind="section_to_finding",
                    weight=section_finding_weight,
                )

                classification_weight = 1.0 / max(1.0, float(len(class_names)))
                for class_name in class_names:
                    class_node_id = f"classification:{class_name}"
                    self._add_property_node(
                        graph,
                        node_id=class_node_id,
                        kind="classification",
                        name=class_name,
                        token_parts=[class_name],
                    )
                    self._add_property_edge(
                        graph,
                        source=finding_node_id,
                        target=class_node_id,
                        kind="finding_to_classification",
                        weight=classification_weight,
                    )

        for validator_names in (
            template.validators.examination_validators,
            template.validators.findings_validators,
            template.validators.classification_validators,
            template.validators.intervention_validators,
            template.validators.unit_validators,
        ):
            for validator_name in validator_names:
                validator_node_id = f"validator:{validator_name}"
                self._add_property_node(
                    graph,
                    node_id=validator_node_id,
                    kind="validator",
                    name=validator_name,
                    token_parts=[validator_name],
                )
                self._add_property_edge(
                    graph,
                    source=template_node_id,
                    target=validator_node_id,
                    kind="template_to_validator",
                    weight=0.4,
                )

        return graph


def _parse_section_finding_ref(
    *,
    finding_ref: Any,
    report_findings: Mapping[str, Any],
) -> tuple[str, list[str]]:
    if isinstance(finding_ref, str):
        report_finding = report_findings.get(finding_ref)
        if report_finding is not None:
            finding_name = str(getattr(report_finding, "finding", finding_ref))
            classifications = [
                str(getattr(c, "classification", ""))
                for c in (getattr(report_finding, "classifications", []) or [])
                if getattr(c, "classification", None)
            ]
            return finding_name, classifications
        return finding_ref, []

    finding_name = str(getattr(finding_ref, "finding", ""))
    classifications = [
        str(getattr(c, "classification", ""))
        for c in (getattr(finding_ref, "classifications", []) or [])
        if getattr(c, "classification", None)
    ]
    return finding_name, classifications


def _section_fields(section: Any) -> list[Any]:
    return list(getattr(section, "fields", []) or [])


def build_report_template_graph(
    template: ReportTemplate,
    *,
    sections: Mapping[str, ReportTemplateSection] | Mapping[str, Any],
    report_findings: Mapping[str, Any],
) -> ReportTemplateGraph:
    """Build the graph of a report template.

    Args:
        template: Template to project.
        sections: Section records by name, used to resolve
            ``template.report_sections``.
        report_findings: :class:`ReportFinding` records by name, used to
            resolve findings that sections reference by name.

    Returns:
        The template graph with sections in report order.
    """
    property_graph = ReportTemplatePropertyGraphAdapter().build(
        template,
        sections=sections,
        report_findings=report_findings,
    )
    nodes_by_id: dict[str, ReportTemplateGraphNode] = {}
    edges: list[ReportTemplateGraphEdge] = []
    template_node_id = f"template:{template.name}"
    section_node_ids: list[str] = []

    for node in property_graph.nodes.values():
        node_type = cast(
            Literal[
                "template",
                "section",
                "finding",
                "classification",
                "validator",
                "patient_field",
                "history_field",
            ],
            node.kind,
        )
        name = str(node.metadata.get("name", node.id))
        _add_node(
            nodes_by_id,
            node_id=node.id,
            node_type=node_type,
            name=name,
            token_source=node.labels,
        )
        if node_type == "section" and node.id in {
            f"section:{section_name}" for section_name in template.report_sections
        }:
            section_node_ids.append(node.id)

    for edge in property_graph.edges:
        edge_type = cast(
            Literal[
                "template_to_section",
                "section_sequence",
                "section_to_finding",
                "section_to_patient_field",
                "section_to_history_field",
                "finding_to_classification",
                "template_to_validator",
            ],
            edge.kind,
        )
        edges.append(
            ReportTemplateGraphEdge(
                source_node_id=edge.source,
                target_node_id=edge.target,
                edge_type=edge_type,
                weight=edge.weight,
            )
        )

    start_node_id = section_node_ids[0] if section_node_ids else template_node_id
    return ReportTemplateGraph(
        template_name=template.name,
        examination=template.examination,
        start_node_id=start_node_id,
        ordered_section_node_ids=section_node_ids,
        nodes=list(nodes_by_id.values()),
        edges=edges,
    )


def _structure_messages(
    language: LanguageCode,
    template: ReportTemplate,
    *collections: Mapping[str, Any],
) -> Callable[..., str]:
    """Bind the shared localized catalogue and concept display names."""
    from lx_dtypes.models.knowledge_base.validators.RuntimeIssues import (
        _runtime_display_names,
        _runtime_message,
    )

    validate_language(language)
    named = [
        item
        for item in (template, *(i for c in collections for i in c.values()))
        if isinstance(getattr(item, "name", None), str)
        and isinstance(getattr(item, "name_de", None), str)
        and isinstance(getattr(item, "name_en", None), str)
    ]
    display_names = _runtime_display_names(language, named)

    def message(key: str, **values: str) -> str:
        return _runtime_message(key, language, display_names=display_names, **values)

    return message


def validate_report_template_structure(
    template: ReportTemplate,
    *,
    sections: Mapping[str, ReportTemplateSection] | Mapping[str, Any],
    report_findings: Mapping[str, Any],
    findings: Mapping[str, Any] | None = None,
    language: LanguageCode = DEFAULT_LANGUAGE,
) -> ReportTemplateStructureValidationResult:
    """Validate one template's structure; messages use display names in ``language``."""
    message = _structure_messages(
        language, template, sections, report_findings, findings or {}
    )
    issues: list[ReportTemplateStructureIssue] = []

    for section_name in template.report_sections:
        if section_name not in sections:
            issues.append(
                ReportTemplateStructureIssue(
                    code="missing_section",
                    level="error",
                    node_id=f"section:{section_name}",
                    message=message(
                        "structure_missing_section",
                        template=template.name,
                        section=section_name,
                    ),
                )
            )

    if len(set(template.report_sections)) != len(template.report_sections):
        issues.append(
            ReportTemplateStructureIssue(
                code="duplicate_section_reference",
                level="warning",
                node_id=f"template:{template.name}",
                message=message(
                    "structure_duplicate_section_reference", template=template.name
                ),
            )
        )

    if not template.report_sections:
        issues.append(
            ReportTemplateStructureIssue(
                code="empty_template_sections",
                level="warning",
                node_id=f"template:{template.name}",
                message=message(
                    "structure_empty_template_sections", template=template.name
                ),
            )
        )

    if findings is None:
        findings = {}

    for section_name in template.report_sections:
        section = sections.get(section_name)
        if section is None:
            continue

        section_kind = str(getattr(section, "section_kind", "findings"))
        section_fields = _section_fields(section)

        if section_kind == "findings" and not section.findings:
            issues.append(
                ReportTemplateStructureIssue(
                    code="empty_section_findings",
                    level="warning",
                    node_id=f"section:{section_name}",
                    message=message(
                        "structure_empty_section_findings", section=section_name
                    ),
                )
            )

        if section_kind not in {"findings", "medications"} and section.findings:
            issues.append(
                ReportTemplateStructureIssue(
                    code="non_finding_section_has_findings",
                    level="warning",
                    node_id=f"section:{section_name}",
                    message=message(
                        "structure_non_finding_section_has_findings",
                        section=section_name,
                        section_kind=section_kind,
                    ),
                )
            )

        if section_kind == "findings" and section_fields:
            issues.append(
                ReportTemplateStructureIssue(
                    code="findings_section_has_fields",
                    level="warning",
                    node_id=f"section:{section_name}",
                    message=message(
                        "structure_findings_section_has_fields", section=section_name
                    ),
                )
            )

        seen_field_keys: set[str] = set()
        for field in section_fields:
            field_key = str(getattr(field, "key", "")).strip()
            if not field_key:
                issues.append(
                    ReportTemplateStructureIssue(
                        code="invalid_section_field",
                        level="error",
                        node_id=f"section:{section_name}",
                        message=message(
                            "structure_invalid_section_field", section=section_name
                        ),
                    )
                )
                continue

            if field_key in seen_field_keys:
                issues.append(
                    ReportTemplateStructureIssue(
                        code="duplicate_section_field",
                        level="warning",
                        node_id=f"section:{section_name}",
                        message=message(
                            "structure_duplicate_section_field",
                            section=section_name,
                            field_key=field_key,
                        ),
                    )
                )
            seen_field_keys.add(field_key)

            if field_key in _PATIENT_DATA_FIELD_KEYS:
                expected_kind = "patient_data"
            elif field_key == "medications":
                expected_kind = "medications"
            elif field_key in _HISTORY_FIELD_KEYS:
                expected_kind = "history"
            else:
                expected_kind = None

            if expected_kind is None:
                issues.append(
                    ReportTemplateStructureIssue(
                        code="unknown_section_field_key",
                        level="warning",
                        node_id=f"section:{section_name}",
                        message=message(
                            "structure_unknown_section_field_key",
                            section=section_name,
                            field_key=field_key,
                        ),
                    )
                )
            elif section_kind != expected_kind:
                issues.append(
                    ReportTemplateStructureIssue(
                        code="section_field_kind_mismatch",
                        level="warning",
                        node_id=f"section:{section_name}",
                        message=message(
                            "structure_section_field_kind_mismatch",
                            field_key=field_key,
                            expected_kind=expected_kind,
                            section_kind=section_kind,
                        ),
                    )
                )

            field_source = getattr(field, "source", None)
            if section_kind == "history" and field_source in {
                "patient",
                "patient_examination",
            }:
                issues.append(
                    ReportTemplateStructureIssue(
                        code="section_field_source_mismatch",
                        level="warning",
                        node_id=f"section:{section_name}",
                        message=message(
                            "structure_history_field_source_mismatch",
                            field_key=field_key,
                            section=section_name,
                            field_source=str(field_source),
                        ),
                    )
                )
            if (
                section_kind in {"patient_data", "medications"}
                and field_source == "history"
            ):
                issues.append(
                    ReportTemplateStructureIssue(
                        code="section_field_source_mismatch",
                        level="warning",
                        node_id=f"section:{section_name}",
                        message=message(
                            "structure_field_history_source_mismatch",
                            field_key=field_key,
                            section=section_name,
                            section_kind=section_kind,
                        ),
                    )
                )

        if section_kind not in {"findings", "medications"}:
            continue

        for finding_ref in section.findings or []:
            finding_name, _ = _parse_section_finding_ref(
                finding_ref=finding_ref,
                report_findings=report_findings,
            )
            if not finding_name:
                issues.append(
                    ReportTemplateStructureIssue(
                        code="invalid_finding_reference",
                        level="error",
                        node_id=f"section:{section_name}",
                        message=message(
                            "structure_invalid_finding_reference", section=section_name
                        ),
                    )
                )
                continue

            if finding_name not in findings:
                issues.append(
                    ReportTemplateStructureIssue(
                        code="unknown_finding_reference",
                        level="warning",
                        node_id=f"finding:{finding_name}",
                        message=message(
                            "structure_unknown_finding_reference",
                            finding=finding_name,
                            template=template.name,
                        ),
                    )
                )

    graph = build_report_template_graph(
        template,
        sections=sections,
        report_findings=report_findings,
    )
    has_errors = any(issue.level == "error" for issue in issues)
    return ReportTemplateStructureValidationResult(
        template_name=template.name,
        ok=not has_errors,
        graph=graph,
        issues=issues,
    )


def validate_report_template_knowledge_base(
    kb: Any,
    *,
    language: LanguageCode = DEFAULT_LANGUAGE,
) -> dict[str, ReportTemplateStructureValidationResult]:
    """Validate the structure of every report template in a knowledge base.

    Args:
        kb: Loaded knowledge base.
        language: Language for issue messages.

    Returns:
        Structural validation results keyed by template name.
    """
    templates = cast(Mapping[str, ReportTemplate], getattr(kb, "report_template", {}))
    sections = cast(Mapping[str, Any], getattr(kb, "report_template_section", {}))
    report_findings = cast(Mapping[str, Any], getattr(kb, "report_finding", {}))
    findings = cast(Mapping[str, Any], getattr(kb, "finding", {}))

    return {
        template_name: validate_report_template_structure(
            template,
            sections=sections,
            report_findings=report_findings,
            findings=findings,
            language=language,
        )
        for template_name, template in templates.items()
    }


__all__ = [
    "ReportTemplateGraph",
    "ReportTemplateGraphEdge",
    "ReportTemplateGraphNode",
    "ReportTemplateStructureIssue",
    "ReportTemplateStructureValidationResult",
    "build_report_template_graph",
    "validate_report_template_knowledge_base",
    "validate_report_template_structure",
]
