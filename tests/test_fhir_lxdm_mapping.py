from lx_dtypes.utils.fhir_lxdm_mapping import (
    TransformationPattern,
    TransformationRule,
    mappings_from_document,
    render_mermaid,
    standard_fhir_lxdm_mappings,
)


def test_standard_patterns_render_many_to_many_flowchart() -> None:
    diagram = render_mermaid(standard_fhir_lxdm_mappings())

    assert diagram.startswith("```mermaid\nflowchart LR")
    assert 'subgraph FHIR["FHIR R4 resource graph"]' in diagram
    assert 'subgraph ADAPTER["LXDM FHIR adapter"]' in diagram
    assert 'subgraph LXDM["LXDM clinical reporting model"]' in diagram
    assert (
        "FHIR_Procedure -->|contributes context| PATTERN_Finding_related_intervention"
    ) in diagram
    assert (
        "FHIR_MedicationAdministration -->|contributes context| "
        "PATTERN_Finding_related_intervention"
    ) in diagram
    assert (
        "PATTERN_Finding_related_intervention -->|constructs or decomposes| "
        "LXDM_PFindingIntervention"
    ) in diagram
    assert "FHIR_MedicationAdministration --> LXDM_PFindingIntervention" not in diagram


def test_standard_patterns_cover_clinical_ledger_concepts() -> None:
    patterns = standard_fhir_lxdm_mappings()
    targets = {target for pattern in patterns for target in pattern.targets}

    assert {
        "LXDM.Patient",
        "LXDM.Case",
        "LXDM.PExamination",
        "LXDM.PFinding",
        "LXDM.PFindingClassifications",
        "LXDM.PFindingIntervention",
        "LXDM.PIndication",
        "LXDM.Examiner",
        "LXDM.Center",
    } <= targets

    intervention = next(
        pattern
        for pattern in patterns
        if pattern.name == "Finding-related intervention"
    )
    assert {
        "FHIR.Procedure",
        "FHIR.MedicationAdministration",
        "FHIR.Device",
        "FHIR.Specimen",
    } <= set(intervention.sources)
    assert any(
        rule.source.startswith("MedicationAdministration")
        and "only when medication was administered" in rule.note
        for rule in intervention.rules
    )


def test_repeated_resources_are_rendered_once() -> None:
    diagram = render_mermaid(
        (
            TransformationPattern(
                "Identity",
                ("FHIR.Patient",),
                ("LXDM.Patient",),
            ),
            TransformationPattern(
                "Examination",
                ("FHIR.Patient", "FHIR.Procedure"),
                ("LXDM.PExamination",),
            ),
        )
    )

    assert diagram.count('FHIR_Patient["Patient"]') == 1
    assert diagram.count('LXDM_Patient["Patient"]') == 1


def test_mapping_document_supports_many_to_many_patterns() -> None:
    patterns = mappings_from_document(
        {
            "patterns": [
                {
                    "name": "Intervention",
                    "sources": ["FHIR.Procedure", "FHIR.MedicationAdministration"],
                    "targets": ["LXDM.PFindingIntervention"],
                    "rules": [
                        {
                            "source": "Procedure.code",
                            "target": "intervention",
                            "note": "primary action",
                        }
                    ],
                }
            ]
        }
    )

    assert patterns == (
        TransformationPattern(
            "Intervention",
            ("FHIR.Procedure", "FHIR.MedicationAdministration"),
            ("LXDM.PFindingIntervention",),
            (
                TransformationRule(
                    "Procedure.code",
                    "intervention",
                    "primary action",
                ),
            ),
        ),
    )
