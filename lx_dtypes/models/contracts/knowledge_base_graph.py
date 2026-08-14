from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any, Literal, Protocol, cast

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic_core import to_jsonable_python

from .core_concepts import CoreConceptCollection
from .json_types import JsonObject
from .knowledge_base import KnowledgeBaseIdentity

KNOWLEDGE_BASE_GRAPH_CONTRACT_VERSION = "knowledge_base_graph_v1"

type GraphNodeKind = Literal[
    "classification",
    "classification_type",
    "classification_choice",
    "classification_choice_descriptor",
    "examination",
    "examination_type",
    "finding",
    "finding_type",
    "indication",
    "indication_type",
    "intervention",
    "intervention_type",
    "unit",
    "unit_type",
    "information_source",
    "information_source_type",
    "citation",
    "report_template",
]
type GraphRelationship = Literal[
    "has_choice",
    "has_descriptor",
    "uses_unit",
    "has_finding",
    "has_indication",
    "has_classification",
    "supports_intervention",
    "caused_by_intervention",
    "is_type",
    "for_examination",
]


class KnowledgeBaseGraphNodeRef(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    kind: GraphNodeKind
    name: str = Field(min_length=1)


class KnowledgeBaseGraphEdge(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    source: KnowledgeBaseGraphNodeRef
    relationship: GraphRelationship
    target: KnowledgeBaseGraphNodeRef


class ReportTemplateGraphProjection(BaseModel):
    """Frontend-stable envelope for a compiled, published report template."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(min_length=1)
    name_de: str | None = None
    name_en: str | None = None
    description: str | None = None
    version: str = Field(min_length=1)
    examination: str = Field(min_length=1)
    guideline_references: list[JsonObject] = Field(default_factory=list)
    coverage_version: str | None = None
    coverage_concepts: list[JsonObject] = Field(default_factory=list)
    report_sections: list[JsonObject] = Field(default_factory=list)
    validators: JsonObject = Field(default_factory=dict)
    lifecycle_status: str = Field(min_length=1)
    readiness: JsonObject = Field(default_factory=dict)
    issues: list[JsonObject] = Field(default_factory=list)


class KnowledgeBaseGraphSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    contract_version: Literal["knowledge_base_graph_v1"] = (
        KNOWLEDGE_BASE_GRAPH_CONTRACT_VERSION
    )
    identity: KnowledgeBaseIdentity
    snapshot_id: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    declaring_modules: list[str] = Field(default_factory=list)
    concepts: CoreConceptCollection
    report_templates: list[ReportTemplateGraphProjection] = Field(default_factory=list)
    edges: list[KnowledgeBaseGraphEdge] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_identity_and_edges(self) -> "KnowledgeBaseGraphSnapshot":
        if self.concepts.knowledge_base_module != self.identity.knowledge_base_module:
            raise ValueError("concept graph module does not match snapshot identity")
        if self.concepts.knowledge_base_version != self.identity.knowledge_base_version:
            raise ValueError("concept graph version does not match snapshot identity")
        _validate_unique_edges(self.edges)
        return self


class ExaminationReportingContext(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    contract_version: Literal["knowledge_base_graph_v1"] = (
        KNOWLEDGE_BASE_GRAPH_CONTRACT_VERSION
    )
    identity: KnowledgeBaseIdentity
    graph_snapshot_id: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    context_id: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    examination_name: str = Field(min_length=1)
    concepts: CoreConceptCollection
    report_templates: list[ReportTemplateGraphProjection] = Field(default_factory=list)
    edges: list[KnowledgeBaseGraphEdge] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_context(self) -> "ExaminationReportingContext":
        examination_names = {item.name for item in self.concepts.examination}
        if examination_names != {self.examination_name}:
            raise ValueError(
                "reporting context must contain exactly its requested examination"
            )
        if any(
            template.examination != self.examination_name
            for template in self.report_templates
        ):
            raise ValueError("reporting context contains a template for another exam")
        _validate_unique_edges(self.edges)
        return self


class _KnowledgeBaseGraphSource(Protocol):
    @property
    def report_template(self) -> Mapping[str, Any]: ...

    def export_core_concepts(self) -> JsonObject: ...

    def export_report_template(self, name: str) -> JsonObject: ...

    def get_report_template_lifecycle_status(self, name: str) -> str: ...


def build_knowledge_base_graph_snapshot(
    kb: _KnowledgeBaseGraphSource,
    *,
    identity: KnowledgeBaseIdentity,
) -> KnowledgeBaseGraphSnapshot:
    concepts_payload = kb.export_core_concepts()
    for collection_name in _concept_collection_names():
        records = concepts_payload.get(collection_name, [])
        if not isinstance(records, list):
            continue
        for record in records:
            if isinstance(record, dict):
                # Runtime/database identifiers are not semantic graph identity and
                # may be regenerated when the same immutable YAML is reloaded.
                record.pop("id", None)
                record.pop("uuid", None)
    concepts = CoreConceptCollection.model_validate(concepts_payload)
    if concepts.knowledge_base_module != identity.knowledge_base_module:
        raise ValueError("loaded core concepts do not match requested module")
    if concepts.knowledge_base_version != identity.knowledge_base_version:
        raise ValueError("loaded core concepts do not match requested version")

    templates = _published_report_templates(kb)
    edges = _build_edges(concepts, templates)
    declaring_modules = sorted(
        {
            identity.knowledge_base_module,
            *(
                record.kb_module_name
                for collection_name in _concept_collection_names()
                for record in getattr(concepts, collection_name)
                if record.kb_module_name
            ),
        }
    )
    content = {
        "contract_version": KNOWLEDGE_BASE_GRAPH_CONTRACT_VERSION,
        "identity": identity.model_dump(mode="json"),
        "declaring_modules": declaring_modules,
        "concepts": concepts.model_dump(mode="json"),
        "report_templates": [item.model_dump(mode="json") for item in templates],
        "edges": [item.model_dump(mode="json") for item in edges],
    }
    return KnowledgeBaseGraphSnapshot(
        **content,
        snapshot_id=_content_hash(content),
    )


def build_examination_reporting_context(
    snapshot: KnowledgeBaseGraphSnapshot,
    *,
    examination_name: str,
) -> ExaminationReportingContext:
    source = snapshot.concepts
    examinations = {examination.name: examination for examination in source.examination}
    examination = examinations.get(examination_name)
    if examination is None:
        raise KeyError(examination_name)

    selected: dict[str, set[str]] = {
        name: set() for name in _concept_collection_names()
    }
    selected["examination"].add(examination_name)
    selected["examination_type"].update(examination.examination_types)
    selected["finding"].update(examination.findings)
    selected["indication"].update(examination.indications)

    records = {
        collection_name: {
            record.name: record for record in getattr(source, collection_name)
        }
        for collection_name in _concept_collection_names()
    }

    for finding_name in sorted(selected["finding"]):
        finding = records["finding"][finding_name]
        selected["finding_type"].update(finding.finding_types)
        selected["classification"].update(finding.classifications)
        selected["intervention"].update(finding.interventions)
        selected["intervention"].update(finding.caused_by_interventions)
    for indication_name in sorted(selected["indication"]):
        indication = records["indication"][indication_name]
        selected["indication_type"].update(indication.indication_types)
        selected["classification"].update(indication.classifications)
        selected["intervention"].update(indication.interventions)
    for classification_name in sorted(selected["classification"]):
        classification = records["classification"][classification_name]
        selected["classification_type"].update(classification.classification_types)
        selected["classification_choice"].update(classification.classification_choices)
    for choice_name in sorted(selected["classification_choice"]):
        choice = records["classification_choice"][choice_name]
        selected["classification_choice_descriptor"].update(
            choice.classification_choice_descriptors
        )
    for descriptor_name in sorted(selected["classification_choice_descriptor"]):
        descriptor = records["classification_choice_descriptor"][descriptor_name]
        if descriptor.unit is not None:
            selected["unit"].add(descriptor.unit)
    for unit_name in sorted(selected["unit"]):
        selected["unit_type"].update(records["unit"][unit_name].unit_types)
    for intervention_name in sorted(selected["intervention"]):
        selected["intervention_type"].update(
            records["intervention"][intervention_name].intervention_types
        )

    # Provenance records do not currently expose reverse concept references, so
    # retain their complete small catalogs in the projection.
    for collection_name in (
        "information_source",
        "information_source_type",
        "citation",
    ):
        selected[collection_name].update(records[collection_name])

    context_concepts = CoreConceptCollection.model_validate(
        {
            "module_name": source.module_name,
            "knowledge_base_module": source.knowledge_base_module,
            "knowledge_base_version": source.knowledge_base_version,
            **{
                collection_name: [
                    records[collection_name][name].model_dump(mode="json")
                    for name in sorted(selected[collection_name])
                ]
                for collection_name in _concept_collection_names()
            },
        }
    )
    templates = [
        template
        for template in snapshot.report_templates
        if template.examination == examination_name
    ]
    included_nodes = {
        (cast(GraphNodeKind, collection_name), record.name)
        for collection_name in _concept_collection_names()
        for record in getattr(context_concepts, collection_name)
    }
    included_nodes.update(("report_template", item.name) for item in templates)
    edges = [
        edge
        for edge in snapshot.edges
        if (edge.source.kind, edge.source.name) in included_nodes
        and (edge.target.kind, edge.target.name) in included_nodes
    ]
    content = {
        "contract_version": KNOWLEDGE_BASE_GRAPH_CONTRACT_VERSION,
        "identity": snapshot.identity.model_dump(mode="json"),
        "graph_snapshot_id": snapshot.snapshot_id,
        "examination_name": examination_name,
        "concepts": context_concepts.model_dump(mode="json"),
        "report_templates": [item.model_dump(mode="json") for item in templates],
        "edges": [item.model_dump(mode="json") for item in edges],
    }
    return ExaminationReportingContext(
        **content,
        context_id=_content_hash(content),
    )


def _published_report_templates(
    kb: _KnowledgeBaseGraphSource,
) -> list[ReportTemplateGraphProjection]:
    templates: list[ReportTemplateGraphProjection] = []
    for template_name in sorted(kb.report_template):
        if kb.get_report_template_lifecycle_status(template_name) != "published":
            continue
        payload = _strip_runtime_metadata(
            to_jsonable_python(kb.export_report_template(template_name))
        )
        templates.append(ReportTemplateGraphProjection.model_validate(payload))
    return templates


def _build_edges(
    concepts: CoreConceptCollection,
    templates: list[ReportTemplateGraphProjection],
) -> list[KnowledgeBaseGraphEdge]:
    edges: list[KnowledgeBaseGraphEdge] = []

    def add(
        source_kind: GraphNodeKind,
        source_name: str,
        relationship: GraphRelationship,
        target_kind: GraphNodeKind,
        target_names: list[str],
    ) -> None:
        edges.extend(
            KnowledgeBaseGraphEdge(
                source=KnowledgeBaseGraphNodeRef(
                    kind=source_kind,
                    name=source_name,
                ),
                relationship=relationship,
                target=KnowledgeBaseGraphNodeRef(kind=target_kind, name=target_name),
            )
            for target_name in target_names
        )

    for record in concepts.classification:
        add(
            "classification",
            record.name,
            "has_choice",
            "classification_choice",
            record.classification_choices,
        )
        add(
            "classification",
            record.name,
            "is_type",
            "classification_type",
            record.classification_types,
        )
    for record in concepts.classification_choice:
        add(
            "classification_choice",
            record.name,
            "has_descriptor",
            "classification_choice_descriptor",
            record.classification_choice_descriptors,
        )
    for record in concepts.classification_choice_descriptor:
        if record.unit is not None:
            add(
                "classification_choice_descriptor",
                record.name,
                "uses_unit",
                "unit",
                [record.unit],
            )
    for record in concepts.examination:
        add("examination", record.name, "has_finding", "finding", record.findings)
        add(
            "examination",
            record.name,
            "has_indication",
            "indication",
            record.indications,
        )
        add(
            "examination",
            record.name,
            "is_type",
            "examination_type",
            record.examination_types,
        )
    for record in concepts.finding:
        add("finding", record.name, "is_type", "finding_type", record.finding_types)
        add(
            "finding",
            record.name,
            "has_classification",
            "classification",
            record.classifications,
        )
        add(
            "finding",
            record.name,
            "supports_intervention",
            "intervention",
            record.interventions,
        )
        add(
            "finding",
            record.name,
            "caused_by_intervention",
            "intervention",
            record.caused_by_interventions,
        )
    for record in concepts.indication:
        add(
            "indication",
            record.name,
            "is_type",
            "indication_type",
            record.indication_types,
        )
        add(
            "indication",
            record.name,
            "has_classification",
            "classification",
            record.classifications,
        )
        add(
            "indication",
            record.name,
            "supports_intervention",
            "intervention",
            record.interventions,
        )
    for record in concepts.intervention:
        add(
            "intervention",
            record.name,
            "is_type",
            "intervention_type",
            record.intervention_types,
        )
    for record in concepts.unit:
        add("unit", record.name, "is_type", "unit_type", record.unit_types)
    for record in concepts.information_source:
        add(
            "information_source",
            record.name,
            "is_type",
            "information_source_type",
            record.information_source_types,
        )
    for template in templates:
        add(
            "report_template",
            template.name,
            "for_examination",
            "examination",
            [template.examination],
        )

    return sorted(
        edges,
        key=lambda edge: (
            edge.source.kind,
            edge.source.name,
            edge.relationship,
            edge.target.kind,
            edge.target.name,
        ),
    )


def _concept_collection_names() -> tuple[str, ...]:
    return tuple(
        field_name
        for field_name in CoreConceptCollection.model_fields
        if field_name
        not in {"module_name", "knowledge_base_module", "knowledge_base_version"}
    )


def _validate_unique_edges(edges: list[KnowledgeBaseGraphEdge]) -> None:
    identities = [
        (
            edge.source.kind,
            edge.source.name,
            edge.relationship,
            edge.target.kind,
            edge.target.name,
        )
        for edge in edges
    ]
    if len(identities) != len(set(identities)):
        raise ValueError("knowledge-base graph edges must be unique")


def _content_hash(payload: dict[str, object]) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def _strip_runtime_metadata(value: Any) -> Any:
    if isinstance(value, list):
        return [_strip_runtime_metadata(item) for item in value]
    if isinstance(value, dict):
        return {
            key: _strip_runtime_metadata(item)
            for key, item in value.items()
            if key not in {"created_at", "id", "source_file", "uuid"}
        }
    return value


__all__ = [
    "KNOWLEDGE_BASE_GRAPH_CONTRACT_VERSION",
    "ExaminationReportingContext",
    "KnowledgeBaseGraphEdge",
    "KnowledgeBaseGraphNodeRef",
    "KnowledgeBaseGraphSnapshot",
    "ReportTemplateGraphProjection",
    "build_examination_reporting_context",
    "build_knowledge_base_graph_snapshot",
]
