from copy import deepcopy
from datetime import UTC, datetime
from uuid import UUID

import pytest
from pydantic import ValidationError

from lx_dtypes.models.contracts.study_analysis import (
    StudyAnalysisDefinition,
    StudyAnalysisUnit,
    StudyFindingReference,
    StudyPredicate,
)
from lx_dtypes.models.interface.KnowledgeBase import KnowledgeBase
from lx_dtypes.models.ledger.p_examination.Pydantic import PExamination
from lx_dtypes.stats import evaluate_study_dataset, validate_study_analysis


@pytest.fixture
def kb() -> KnowledgeBase:
    return KnowledgeBase.model_validate(
        {
            "config": {"name": "synthetic", "version": "1.0.0"},
            "finding": {
                "lesion": {
                    "name": "lesion",
                    "classifications": ["technique", "margin", "size"],
                }
            },
            "examination": {"exam": {"name": "exam", "findings": ["lesion"]}},
            "classification": {
                "technique": {
                    "name": "technique",
                    "classification_choices": ["emr", "esd"],
                },
                "margin": {
                    "name": "margin",
                    "classification_choices": ["r0", "r1", "rx"],
                },
                "size": {"name": "size", "classification_choices": ["size_mm"]},
            },
            "classification_choice": {
                name: {
                    "name": name,
                    "classification_choice_descriptors": ["mm"]
                    if name == "size_mm"
                    else [],
                }
                for name in ["emr", "esd", "r0", "r1", "rx", "size_mm"]
            },
            "classification_choice_descriptor": {
                "mm": {"name": "mm", "numeric_min": 0.0, "numeric_max": 100.0}
            },
        }
    )


def rule(classification: str, value: str) -> dict[str, object]:
    return {
        "predicates": [
            {"classification": classification, "operator": "eq", "value": value}
        ]
    }


@pytest.fixture
def definition() -> StudyAnalysisDefinition:
    return StudyAnalysisDefinition.model_validate(
        {
            "name": "margin_comparison",
            "module": "synthetic",
            "version": "1.0.0",
            "unit_finding": "lesion",
            "status": "ready",
            "inclusion": {
                "predicates": [
                    {
                        "classification": "size",
                        "descriptor": "mm",
                        "operator": "ge",
                        "value": 20,
                    }
                ]
            },
            "groups": [
                {"name": name, "rule": rule("technique", name)}
                for name in ["emr", "esd"]
            ],
            "endpoints": [
                {
                    "name": "r0",
                    "positive": rule("margin", "r0"),
                    "negative": rule("margin", "r1"),
                }
            ],
        }
    )


def observation(
    number: int,
    *,
    technique: str = "emr",
    margin: str | None = "r0",
    size: float | None = 20.0,
) -> PExamination:
    record_id, finding_id, group_id = (
        str(UUID(int=number * 100 + offset)) for offset in range(3)
    )
    choices: list[dict[str, object]] = [
        {
            "classification": "technique",
            "classification_choice": technique,
            "patient_finding_classifications": group_id,
        }
    ]
    if margin is not None:
        choices.append(
            {
                "classification": "margin",
                "classification_choice": margin,
                "patient_finding_classifications": group_id,
            }
        )
    if size is not None:
        choice_id = str(UUID(int=number * 100 + 3))
        choices.append(
            {
                "uuid": choice_id,
                "classification": "size",
                "classification_choice": "size_mm",
                "patient_finding_classifications": group_id,
                "patient_finding_classification_choice_descriptors": [
                    {
                        "classification_choice_descriptor": "mm",
                        "descriptor_value": size,
                        "patient_finding_classification_choice": choice_id,
                    }
                ],
            }
        )
    return PExamination.model_validate(
        {
            "uuid": record_id,
            "patient": "synthetic",
            "examination": "exam",
            "date": datetime(2026, 1, 1, tzinfo=UTC),
            "knowledge_base_module": "synthetic",
            "knowledge_base_version": "1.0.0",
            "patient_findings": [
                {
                    "uuid": finding_id,
                    "finding": "lesion",
                    "patient_examination": record_id,
                    "patient_finding_classifications": [
                        {
                            "uuid": group_id,
                            "patient_finding": finding_id,
                            "patient_finding_classification_choices": choices,
                        }
                    ],
                }
            ],
        }
    )


def test_descriptive_counts_exclude_missing_and_rx_from_denominator(
    kb: KnowledgeBase, definition: StudyAnalysisDefinition
) -> None:
    records = [
        observation(1),
        observation(2, margin="r1"),
        observation(3, margin="rx"),
        observation(4, margin=None),
        observation(5, size=19),
        observation(6, size=None),
    ]
    result = evaluate_study_dataset(definition, records, kb)
    assert (
        result.total_units,
        result.included_units,
        result.excluded_units,
        result.inclusion_unknown,
    ) == (6, 4, 1, 1)
    emr, esd = result.endpoints
    assert (emr.numerator, emr.denominator, emr.negative, emr.missing, emr.rate) == (
        1,
        2,
        1,
        2,
        0.5,
    )
    assert esd.denominator == 0 and esd.rate is None
    assert result == evaluate_study_dataset(definition, list(reversed(records)), kb)
    assert result.analysis_digest.startswith("sha256:")


def test_mutable_records_are_revalidated(
    kb: KnowledgeBase, definition: StudyAnalysisDefinition
) -> None:
    record = observation(1)
    record.patient_findings[0].finding = "absent"
    with pytest.raises(ValueError, match="invalid ledger"):
        evaluate_study_dataset(definition, [record], kb)


@pytest.mark.parametrize(
    "change",
    [
        {"operator": "exec"},
        {"operator": "ge", "value": "20"},
        {"operator": "ge", "descriptor": None},
        {"operator": "present", "value": 20},
        {"operator": "in", "value": []},
        {"operator": "eq", "value": float("inf")},
    ],
)
def test_rejects_unsupported_predicates(change: dict[str, object]) -> None:
    payload = {
        "classification": "size",
        "descriptor": "mm",
        "operator": "ge",
        "value": 20,
        **change,
    }
    with pytest.raises(ValidationError):
        StudyPredicate.model_validate(payload)


def test_draft_and_wrong_kb_and_unknown_choice_rejected(
    kb: KnowledgeBase, definition: StudyAnalysisDefinition
) -> None:
    definition.status = "draft"
    validate_study_analysis(definition, kb)
    with pytest.raises(ValueError, match="draft"):
        evaluate_study_dataset(definition, [], kb)
    definition.status = "ready"
    definition.version = "2.0.0"
    with pytest.raises(ValueError, match="identity"):
        evaluate_study_dataset(definition, [], kb)
    definition.version = "1.0.0"
    definition.groups[0].rule.predicates[0].value = "unknown"
    with pytest.raises(ValueError, match="choice"):
        validate_study_analysis(definition, kb)


def test_duplicate_records_and_units_rejected(
    kb: KnowledgeBase, definition: StudyAnalysisDefinition
) -> None:
    record = observation(1)
    with pytest.raises(ValueError, match="duplicate dataset"):
        evaluate_study_dataset(definition, [record, record], kb)
    unit = StudyAnalysisUnit(
        index=StudyFindingReference(
            record_uuid=str(record.uuid),
            finding_uuid=str(record.patient_findings[0].uuid),
        )
    )
    with pytest.raises(ValueError, match="duplicate index"):
        evaluate_study_dataset(definition, [record], kb, units=[unit, unit])


def test_missing_ne_is_unknown_and_any_respects_three_values(
    kb: KnowledgeBase, definition: StudyAnalysisDefinition
) -> None:
    assert definition.inclusion is not None
    definition.inclusion.predicates[0].operator = "ne"
    definition.inclusion.predicates[0].value = 10.0
    result = evaluate_study_dataset(definition, [observation(1, size=None)], kb)
    assert result.inclusion_unknown == 1
    definition.inclusion.mode = "any"
    definition.inclusion.predicates.append(
        StudyPredicate(classification="technique", operator="eq", value="emr")
    )
    result = evaluate_study_dataset(definition, [observation(1, size=None)], kb)
    assert result.included_units == 1


def test_ambiguous_groups_and_conflicting_endpoints_are_counted(
    kb: KnowledgeBase, definition: StudyAnalysisDefinition
) -> None:
    definition.groups[1].rule = deepcopy(definition.groups[0].rule)
    result = evaluate_study_dataset(definition, [observation(1)], kb)
    assert result.ambiguous_units == 1 and result.included_units == 0
    definition.groups.pop()
    definition.endpoints[0].negative = deepcopy(definition.endpoints[0].positive)
    result = evaluate_study_dataset(definition, [observation(1)], kb)
    assert result.endpoints[0].conflicting == 1 and result.endpoints[0].denominator == 0


def test_explicit_units_reject_cross_patient_and_reverse_dates(
    kb: KnowledgeBase, definition: StudyAnalysisDefinition
) -> None:
    first, second = observation(1), observation(2)
    unit = StudyAnalysisUnit(
        index=StudyFindingReference(
            record_uuid=str(first.uuid),
            finding_uuid=str(first.patient_findings[0].uuid),
        ),
        follow_up=StudyFindingReference(
            record_uuid=str(second.uuid),
            finding_uuid=str(second.patient_findings[0].uuid),
        ),
    )
    second.patient = "another"
    with pytest.raises(ValueError, match="crosses patient"):
        evaluate_study_dataset(definition, [first, second], kb, units=[unit])
    second.patient = first.patient
    with pytest.raises(ValueError, match="strictly ordered"):
        evaluate_study_dataset(definition, [first, second], kb, units=[unit])


def test_wrong_ledger_identity_rejected(
    kb: KnowledgeBase, definition: StudyAnalysisDefinition
) -> None:
    record = observation(1)
    record.knowledge_base_version = None
    with pytest.raises(ValueError, match="exact analysis"):
        evaluate_study_dataset(definition, [record], kb)


def test_shipped_coloreg_r0_plan_evaluates_linked_polyp_size() -> None:
    from pathlib import Path

    import yaml

    from lx_dtypes.models.contracts.study_setup import StudySetupDefinition
    from lx_dtypes.packages import load_package

    setup = StudySetupDefinition.model_validate(
        yaml.safe_load(
            Path("lx_dtypes/data/study_metadata/coloreg_resection.yml").read_text()
        )
    )
    definition = next(
        cohort for cohort in setup.cohorts if cohort.definition_id == "coloreg_r0"
    ).study_metadata.analysis_definitions[0]
    kb = load_package(Path("lx_dtypes/data/report_templates/coloreg/config.yaml"))
    record = observation(1)
    record.examination = "colonoscopy"
    record.knowledge_base_module = "coloreg"
    record.knowledge_base_version = "0.3.0"
    finding = record.patient_findings[0]
    finding.finding = "coloreg_polyp_resection"
    choices = finding.patient_finding_classifications[
        0
    ].patient_finding_classification_choices
    choices[0].classification = "coloreg_resection_technique"
    choices[0].classification_choice = "coloreg_technique_emr"
    choices[1].classification = "coloreg_histological_margin_status"
    choices[1].classification_choice = "coloreg_margin_r0"
    size = choices.pop()
    size.classification = "lesion_size_mm"
    size.classification_choice = "lesion_size_oval_mm"
    size.patient_finding_classification_choice_descriptors[
        0
    ].classification_choice_descriptor = "lesion_size_mm_value"
    polyp = deepcopy(finding)
    polyp.uuid = UUID(int=999)
    polyp.finding = "colon_polyp"
    polyp.patient_finding_classifications[0].patient_finding_classification_choices = [
        size
    ]
    record.patient_findings.append(polyp)
    unit = StudyAnalysisUnit(
        index=StudyFindingReference(
            record_uuid=str(record.uuid), finding_uuid=str(finding.uuid)
        ),
        polyp=StudyFindingReference(
            record_uuid=str(record.uuid), finding_uuid=str(polyp.uuid)
        ),
    )
    result = evaluate_study_dataset(definition, [record], kb, units=[unit])
    r0 = next(
        item
        for item in result.endpoints
        if item.endpoint == "histological_r0_among_assessable" and item.group == "EMR"
    )
    assert (r0.numerator, r0.denominator, r0.rate) == (1, 1, 1.0)
