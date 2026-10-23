"""Describe context-dependent transformation patterns between FHIR and LXDM.

FHIR represents exchange content as a graph of fine-grained resources. LXDM
organizes data around clinician-facing reporting elements. A transformation
therefore aggregates or decomposes resource graphs; it is not an assertion
that one FHIR resource is semantically equivalent to one LXDM class.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class TransformationRule:
    """One reviewable rule within a resource-graph transformation pattern."""

    source: str
    target: str
    note: str = ""


@dataclass(frozen=True)
class TransformationPattern:
    """A many-to-many transformation between FHIR resources and LXDM concepts."""

    name: str
    sources: tuple[str, ...]
    targets: tuple[str, ...]
    rules: tuple[TransformationRule, ...] = ()
    note: str = ""


def _safe_id(value: str) -> str:
    return "".join(char if char.isalnum() or char == "_" else "_" for char in value)


def _label(value: str) -> str:
    return value.replace('"', "'").replace("\n", " ")


def render_mermaid(
    patterns: Iterable[TransformationPattern],
    *,
    title: str = "FHIR resource graphs to LXDM clinical reporting elements",
) -> str:
    """Render many-to-many transformation patterns as a Mermaid flowchart."""

    transformation_patterns = tuple(patterns)
    if not transformation_patterns:
        raise ValueError("At least one transformation pattern is required")

    sources = tuple(
        dict.fromkeys(
            source for pattern in transformation_patterns for source in pattern.sources
        )
    )
    targets = tuple(
        dict.fromkeys(
            target for pattern in transformation_patterns for target in pattern.targets
        )
    )

    lines = [
        "```mermaid",
        "flowchart LR",
        f"  %% {_label(title)}",
        '  subgraph FHIR["FHIR R4 resource graph"]',
    ]
    for source in sources:
        lines.append(
            f'    {_safe_id(source)}["{_label(source.removeprefix("FHIR."))}"]'
        )
    lines.extend(["  end", '  subgraph ADAPTER["LXDM FHIR adapter"]'])
    for pattern in transformation_patterns:
        pattern_id = f"PATTERN_{_safe_id(pattern.name)}"
        rules = "<br/>".join(
            f"{_label(rule.source)} → {_label(rule.target)}"
            + (f" ({_label(rule.note)})" if rule.note else "")
            for rule in pattern.rules
        )
        label = _label(pattern.name)
        if rules:
            label += f"<br/><small>{rules}</small>"
        lines.append(f'    {pattern_id}["{label}"]')
    lines.extend(["  end", '  subgraph LXDM["LXDM clinical reporting model"]'])
    for target in targets:
        lines.append(
            f'    {_safe_id(target)}["{_label(target.removeprefix("LXDM."))}"]'
        )
    lines.append("  end")
    lines.append("")

    for pattern in transformation_patterns:
        pattern_id = f"PATTERN_{_safe_id(pattern.name)}"
        for source in pattern.sources:
            lines.append(f"  {_safe_id(source)} -->|contributes context| {pattern_id}")
        for target in pattern.targets:
            lines.append(
                f"  {pattern_id} -->|constructs or decomposes| {_safe_id(target)}"
            )
    lines.extend(
        [
            "",
            "  classDef fhir fill:#e8f1ff,stroke:#2f6fba,color:#172033",
            "  classDef adapter fill:#fff0c9,stroke:#a16207,color:#172033",
            "  classDef lxdm fill:#eaf8ed,stroke:#2d7a46,color:#172033",
            "  class " + ",".join(_safe_id(source) for source in sources) + " fhir",
            "  class "
            + ",".join(
                f"PATTERN_{_safe_id(pattern.name)}"
                for pattern in transformation_patterns
            )
            + " adapter",
            "  class " + ",".join(_safe_id(target) for target in targets) + " lxdm",
            "```",
        ]
    )
    return "\n".join(lines) + "\n"


def standard_fhir_lxdm_mappings() -> tuple[TransformationPattern, ...]:
    """Return clinical transformation patterns for FHIR R4 and the LXDM Ledger."""

    return (
        TransformationPattern(
            "Patient and case context",
            ("FHIR.Patient", "FHIR.Encounter", "FHIR.Organization"),
            ("LXDM.Patient", "LXDM.Case", "LXDM.Center"),
            (
                TransformationRule(
                    "Patient.identifier/name/birthDate/gender/contact",
                    "Patient identity and demographics",
                ),
                TransformationRule(
                    "Encounter.subject/period",
                    "Case membership and dates",
                ),
                TransformationRule(
                    "Patient.managingOrganization + Encounter.serviceProvider",
                    "Center relationship",
                    "resolved by references",
                ),
            ),
            "Identity, episode, and organization references are resolved as a graph.",
        ),
        TransformationPattern(
            "Examination and report context",
            ("FHIR.Procedure", "FHIR.DiagnosticReport", "FHIR.Encounter"),
            ("LXDM.PExamination",),
            (
                TransformationRule(
                    "Procedure.code/subject/encounter/performed[x]",
                    "PExamination examination/patient/case/date",
                ),
                TransformationRule(
                    "DiagnosticReport.code/effective[x]/result",
                    "PExamination report context and finding links",
                ),
            ),
            "The performed examination and its report contribute complementary context.",
        ),
        TransformationPattern(
            "Clinical indication",
            (
                "FHIR.ServiceRequest",
                "FHIR.Condition",
                "FHIR.Observation",
            ),
            ("LXDM.PIndication",),
            (
                TransformationRule(
                    "ServiceRequest.code/reasonCode/reasonReference",
                    "PIndication concept and classifications",
                ),
                TransformationRule(
                    "Referenced Condition or Observation",
                    "PIndication clinical reason",
                    "terminology and profile dependent",
                ),
            ),
            "Requested service and referenced clinical reasons form one reporting element.",
        ),
        TransformationPattern(
            "Clinical finding",
            (
                "FHIR.Observation",
                "FHIR.Condition",
                "FHIR.DiagnosticReport",
            ),
            ("LXDM.PFinding", "LXDM.PFindingClassifications"),
            (
                TransformationRule(
                    "Observation.code/value[x]/component",
                    "PFinding and classifications",
                ),
                TransformationRule(
                    "Condition.code/clinicalStatus",
                    "PFinding and status classification",
                ),
                TransformationRule(
                    "DiagnosticReport.result",
                    "PExamination-to-finding links",
                    "reference resolution",
                ),
            ),
            "Coded and measured values are normalized into clinician-facing findings.",
        ),
        TransformationPattern(
            "Finding-related intervention",
            (
                "FHIR.Procedure",
                "FHIR.MedicationAdministration",
                "FHIR.Device",
                "FHIR.DiagnosticReport",
                "FHIR.Specimen",
            ),
            ("LXDM.PFindingIntervention",),
            (
                TransformationRule(
                    "Procedure.code/bodySite/reasonReference",
                    "Intervention concept and finding relation",
                    "primary performed-action context",
                ),
                TransformationRule(
                    "MedicationAdministration.medication[x]/effective[x]",
                    "Medication detail",
                    "only when medication was administered",
                ),
                TransformationRule(
                    "Procedure.focalDevice/usedReference + Device",
                    "Device detail",
                    "only when a device is clinically relevant",
                ),
                TransformationRule(
                    "DiagnosticReport.specimen + Specimen",
                    "Specimen context",
                    "only for sampling interventions",
                ),
            ),
            "Several FHIR resources may construct one intervention, and one resource may contribute to several clinical elements.",
        ),
        TransformationPattern(
            "Performer and center context",
            (
                "FHIR.Practitioner",
                "FHIR.PractitionerRole",
                "FHIR.Organization",
                "FHIR.Procedure",
            ),
            ("LXDM.Examiner", "LXDM.Center"),
            (
                TransformationRule(
                    "Procedure.performer.actor",
                    "Examiner relation",
                    "reference resolution",
                ),
                TransformationRule(
                    "Practitioner + PractitionerRole",
                    "Examiner identity and role",
                ),
                TransformationRule(
                    "PractitionerRole.organization + Organization",
                    "Center",
                ),
            ),
            "Person, role, organization, and performed-action context are combined.",
        ),
    )


def _rule(data: Mapping[str, Any]) -> TransformationRule:
    try:
        return TransformationRule(
            source=str(data["source"]),
            target=str(data["target"]),
            note=str(data.get("note", "")),
        )
    except KeyError as err:
        raise ValueError(f"Transformation rule is missing required key: {err}") from err


def mappings_from_document(
    document: Mapping[str, Any],
) -> tuple[TransformationPattern, ...]:
    """Load many-to-many patterns from a JSON/YAML-compatible document."""

    raw_patterns = document.get("patterns")
    if not isinstance(raw_patterns, list):
        raise TypeError("Mapping document must contain a 'patterns' list")
    result: list[TransformationPattern] = []
    for idx, raw in enumerate(raw_patterns):
        if not isinstance(raw, Mapping):
            raise TypeError(f"Pattern at index {idx} must be an object")
        try:
            sources = raw["sources"]
            targets = raw["targets"]
            if not isinstance(sources, list) or not isinstance(targets, list):
                raise TypeError(
                    f"Pattern at index {idx} requires list-valued sources and targets"
                )
            result.append(
                TransformationPattern(
                    name=str(raw["name"]),
                    sources=tuple(map(str, sources)),
                    targets=tuple(map(str, targets)),
                    rules=tuple(_rule(item) for item in raw.get("rules", [])),
                    note=str(raw.get("note", "")),
                )
            )
        except KeyError as err:
            raise ValueError(f"Pattern at index {idx} missing key: {err}") from err
    return tuple(result)


def write_mermaid(
    path: str | Path,
    patterns: Iterable[TransformationPattern],
    *,
    title: str = "FHIR resource graphs to LXDM clinical reporting elements",
) -> Path:
    """Write a Mermaid transformation diagram and return its output path."""

    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_mermaid(patterns, title=title), encoding="utf-8")
    return output


__all__ = [
    "TransformationPattern",
    "TransformationRule",
    "mappings_from_document",
    "render_mermaid",
    "standard_fhir_lxdm_mappings",
    "write_mermaid",
]
