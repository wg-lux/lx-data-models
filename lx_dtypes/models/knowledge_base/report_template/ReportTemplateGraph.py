from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal, Mapping, cast

from pydantic import BaseModel, Field

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


class ReportTemplateGraphNode(BaseModel):
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
        return cast(ReportTemplateGraphNodeDataDict, self.model_dump(mode="python"))


class ReportTemplateGraphEdge(BaseModel):
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
        return cast(ReportTemplateGraphEdgeDataDict, self.model_dump(mode="python"))


class ReportTemplateGraph(BaseModel):
    template_name: str
    examination: str
    start_node_id: str
    ordered_section_node_ids: list[str] = Field(default_factory=list)
    nodes: list[ReportTemplateGraphNode] = Field(default_factory=list)
    edges: list[ReportTemplateGraphEdge] = Field(default_factory=list)

    def as_ddict(self) -> ReportTemplateGraphDataDict:
        return cast(ReportTemplateGraphDataDict, self.model_dump(mode="python"))


class ReportTemplateStructureIssue(BaseModel):
    code: str
    message: str
    level: Literal["error", "warning"] = "error"
    node_id: str | None = None

    def as_ddict(self) -> ReportTemplateStructureIssueDataDict:
        return cast(
            ReportTemplateStructureIssueDataDict, self.model_dump(mode="python")
        )


class ReportTemplateStructureValidationResult(BaseModel):
    template_name: str
    ok: bool
    graph: ReportTemplateGraph
    issues: list[ReportTemplateStructureIssue] = Field(default_factory=list)

    def as_ddict(self) -> ReportTemplateStructureValidationResultDataDict:
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
    sections: Mapping[str, "ReportTemplateSection"] | Mapping[str, Any],
    report_findings: Mapping[str, Any],
) -> ReportTemplateGraph:
    nodes_by_id: dict[str, ReportTemplateGraphNode] = {}
    edges: list[ReportTemplateGraphEdge] = []

    template_node_id = f"template:{template.name}"
    _add_node(
        nodes_by_id,
        node_id=template_node_id,
        node_type="template",
        name=template.name,
        token_source=(
            _tokenize(template.name)
            + _tokenize(template.examination)
            + [
                token
                for v_name in template.validators.examination_validators
                for token in _tokenize(v_name)
            ]
            + [
                token
                for v_name in template.validators.findings_validators
                for token in _tokenize(v_name)
            ]
            + [
                token
                for v_name in template.validators.classification_validators
                for token in _tokenize(v_name)
            ]
            + [
                token
                for v_name in template.validators.intervention_validators
                for token in _tokenize(v_name)
            ]
            + [
                token
                for v_name in template.validators.unit_validators
                for token in _tokenize(v_name)
            ]
        ),
    )

    section_node_ids: list[str] = []
    prev_section_node_id: str | None = None

    for section_name in template.report_sections:
        section = sections.get(section_name)
        if section is None:
            continue

        section_node_id = f"section:{section_name}"
        section_node_ids.append(section_node_id)

        _add_node(
            nodes_by_id,
            node_id=section_node_id,
            node_type="section",
            name=section_name,
            token_source=_tokenize(section_name)
            + [
                token
                for section_type in section.types
                for token in _tokenize(section_type)
            ]
            + _tokenize(getattr(section, "section_kind", "findings"))
            + [
                token
                for field in _section_fields(section)
                for token in _tokenize(str(getattr(field, "key", "")))
            ],
        )

        edges.append(
            ReportTemplateGraphEdge(
                source_node_id=template_node_id,
                target_node_id=section_node_id,
                edge_type="template_to_section",
                weight=1.0,
            )
        )

        if prev_section_node_id is not None:
            edges.append(
                ReportTemplateGraphEdge(
                    source_node_id=prev_section_node_id,
                    target_node_id=section_node_id,
                    edge_type="section_sequence",
                    weight=1.0,
                )
            )
        prev_section_node_id = section_node_id

        section_kind = str(getattr(section, "section_kind", "findings"))
        field_refs = _section_fields(section)
        section_field_weight = 1.0 / max(1.0, float(len(field_refs)))
        for field in field_refs:
            field_key = str(getattr(field, "key", ""))
            if not field_key:
                continue

            if section_kind == "patient_data":
                field_node_type: Literal["patient_field", "history_field"] = (
                    "patient_field"
                )
                field_node_id = f"patient_field:{field_key}"
                field_edge_type: Literal[
                    "section_to_patient_field", "section_to_history_field"
                ] = "section_to_patient_field"
            elif section_kind == "history":
                field_node_type = "history_field"
                field_node_id = f"history_field:{field_key}"
                field_edge_type = "section_to_history_field"
            else:
                continue

            _add_node(
                nodes_by_id,
                node_id=field_node_id,
                node_type=field_node_type,
                name=field_key,
                token_source=_tokenize(field_key),
            )
            edges.append(
                ReportTemplateGraphEdge(
                    source_node_id=section_node_id,
                    target_node_id=field_node_id,
                    edge_type=field_edge_type,
                    weight=section_field_weight,
                )
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
            _add_node(
                nodes_by_id,
                node_id=finding_node_id,
                node_type="finding",
                name=finding_name,
                token_source=_tokenize(finding_name),
            )

            edges.append(
                ReportTemplateGraphEdge(
                    source_node_id=section_node_id,
                    target_node_id=finding_node_id,
                    edge_type="section_to_finding",
                    weight=section_finding_weight,
                )
            )

            classification_weight = 1.0 / max(1.0, float(len(class_names)))
            for class_name in class_names:
                class_node_id = f"classification:{class_name}"
                _add_node(
                    nodes_by_id,
                    node_id=class_node_id,
                    node_type="classification",
                    name=class_name,
                    token_source=_tokenize(class_name),
                )
                edges.append(
                    ReportTemplateGraphEdge(
                        source_node_id=finding_node_id,
                        target_node_id=class_node_id,
                        edge_type="finding_to_classification",
                        weight=classification_weight,
                    )
                )

    for validator_name in template.validators.examination_validators:
        validator_node_id = f"validator:{validator_name}"
        _add_node(
            nodes_by_id,
            node_id=validator_node_id,
            node_type="validator",
            name=validator_name,
            token_source=_tokenize(validator_name),
        )
        edges.append(
            ReportTemplateGraphEdge(
                source_node_id=template_node_id,
                target_node_id=validator_node_id,
                edge_type="template_to_validator",
                weight=0.4,
            )
        )

    for validator_name in template.validators.findings_validators:
        validator_node_id = f"validator:{validator_name}"
        _add_node(
            nodes_by_id,
            node_id=validator_node_id,
            node_type="validator",
            name=validator_name,
            token_source=_tokenize(validator_name),
        )
        edges.append(
            ReportTemplateGraphEdge(
                source_node_id=template_node_id,
                target_node_id=validator_node_id,
                edge_type="template_to_validator",
                weight=0.4,
            )
        )

    for validator_name in template.validators.classification_validators:
        validator_node_id = f"validator:{validator_name}"
        _add_node(
            nodes_by_id,
            node_id=validator_node_id,
            node_type="validator",
            name=validator_name,
            token_source=_tokenize(validator_name),
        )
        edges.append(
            ReportTemplateGraphEdge(
                source_node_id=template_node_id,
                target_node_id=validator_node_id,
                edge_type="template_to_validator",
                weight=0.4,
            )
        )

    for validator_name in template.validators.intervention_validators:
        validator_node_id = f"validator:{validator_name}"
        _add_node(
            nodes_by_id,
            node_id=validator_node_id,
            node_type="validator",
            name=validator_name,
            token_source=_tokenize(validator_name),
        )
        edges.append(
            ReportTemplateGraphEdge(
                source_node_id=template_node_id,
                target_node_id=validator_node_id,
                edge_type="template_to_validator",
                weight=0.4,
            )
        )

    for validator_name in template.validators.unit_validators:
        validator_node_id = f"validator:{validator_name}"
        _add_node(
            nodes_by_id,
            node_id=validator_node_id,
            node_type="validator",
            name=validator_name,
            token_source=_tokenize(validator_name),
        )
        edges.append(
            ReportTemplateGraphEdge(
                source_node_id=template_node_id,
                target_node_id=validator_node_id,
                edge_type="template_to_validator",
                weight=0.4,
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


def validate_report_template_structure(
    template: ReportTemplate,
    *,
    sections: Mapping[str, "ReportTemplateSection"] | Mapping[str, Any],
    report_findings: Mapping[str, Any],
    findings: Mapping[str, Any] | None = None,
) -> ReportTemplateStructureValidationResult:
    issues: list[ReportTemplateStructureIssue] = []

    for section_name in template.report_sections:
        if section_name not in sections:
            issues.append(
                ReportTemplateStructureIssue(
                    code="missing_section",
                    level="error",
                    node_id=f"section:{section_name}",
                    message=(
                        f"Template '{template.name}' references unknown section "
                        f"'{section_name}'."
                    ),
                )
            )

    if len(set(template.report_sections)) != len(template.report_sections):
        issues.append(
            ReportTemplateStructureIssue(
                code="duplicate_section_reference",
                level="warning",
                node_id=f"template:{template.name}",
                message=(
                    f"Template '{template.name}' references at least one section "
                    "more than once."
                ),
            )
        )

    if not template.report_sections:
        issues.append(
            ReportTemplateStructureIssue(
                code="empty_template_sections",
                level="warning",
                node_id=f"template:{template.name}",
                message=f"Template '{template.name}' has no report sections.",
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
                    message=f"Section '{section_name}' has no findings.",
                )
            )

        if section_kind != "findings" and section.findings:
            issues.append(
                ReportTemplateStructureIssue(
                    code="non_finding_section_has_findings",
                    level="warning",
                    node_id=f"section:{section_name}",
                    message=(
                        f"Section '{section_name}' is '{section_kind}' but also defines "
                        "findings."
                    ),
                )
            )

        if section_kind == "findings" and section_fields:
            issues.append(
                ReportTemplateStructureIssue(
                    code="findings_section_has_fields",
                    level="warning",
                    node_id=f"section:{section_name}",
                    message=(
                        f"Section '{section_name}' is a findings section but also "
                        "defines metadata fields."
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
                        message=(
                            f"Section '{section_name}' contains a field without a key."
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
                        message=(
                            f"Section '{section_name}' contains duplicate field key "
                            f"'{field_key}'."
                        ),
                    )
                )
            seen_field_keys.add(field_key)

            if field_key in _PATIENT_DATA_FIELD_KEYS:
                expected_kind = "patient_data"
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
                        message=(
                            f"Section '{section_name}' uses unknown field key "
                            f"'{field_key}'."
                        ),
                    )
                )
            elif section_kind != expected_kind:
                issues.append(
                    ReportTemplateStructureIssue(
                        code="section_field_kind_mismatch",
                        level="warning",
                        node_id=f"section:{section_name}",
                        message=(
                            f"Field '{field_key}' is intended for '{expected_kind}' "
                            f"sections but is used in '{section_kind}'."
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
                        message=(
                            f"Field '{field_key}' in history section '{section_name}' "
                            f"uses source '{field_source}'."
                        ),
                    )
                )
            if section_kind == "patient_data" and field_source == "history":
                issues.append(
                    ReportTemplateStructureIssue(
                        code="section_field_source_mismatch",
                        level="warning",
                        node_id=f"section:{section_name}",
                        message=(
                            f"Field '{field_key}' in patient_data section "
                            f"'{section_name}' uses source 'history'."
                        ),
                    )
                )

        if section_kind != "findings":
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
                        message=(
                            f"Section '{section_name}' contains an invalid finding "
                            "reference."
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
                        message=(
                            f"Finding '{finding_name}' is used by template "
                            f"'{template.name}' but is not present in the knowledge base."
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
) -> dict[str, ReportTemplateStructureValidationResult]:
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
        )
        for template_name, template in templates.items()
    }


__all__ = [
    "ReportTemplateGraphNode",
    "ReportTemplateGraphEdge",
    "ReportTemplateGraph",
    "ReportTemplateStructureIssue",
    "ReportTemplateStructureValidationResult",
    "build_report_template_graph",
    "validate_report_template_structure",
    "validate_report_template_knowledge_base",
]
