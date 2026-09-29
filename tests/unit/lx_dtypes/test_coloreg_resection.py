"""Exercise versioned ColoReg capture semantics and lesion-local requirements."""

from __future__ import annotations

from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

import pytest
import yaml

from lx_dtypes.knowledge_bases import get_packaged_knowledge_base
from lx_dtypes.models.interface.data_roots import package_data_root
from lx_dtypes.models.interface.DataLoader import DataLoader
from lx_dtypes.models.interface.KnowledgeBase import KnowledgeBase
from lx_dtypes.models.knowledge_base.report_template.ReportConceptCoverageBuilder import (
    build_report_concept_coverage,
)
from lx_dtypes.models.knowledge_base.report_template.ValidatorRuntime import (
    evaluate_findings_validator_runtime,
)
from lx_dtypes.models.ledger.p_examination import PExamination
from lx_dtypes.models.ledger.p_finding import PFinding
from lx_dtypes.models.ledger.p_finding_classification_choice import (
    PFindingClassificationChoice,
)
from lx_dtypes.models.ledger.p_finding_classification_choice_descriptor import (
    PFindingClassificationChoiceDescriptor,
)
from lx_dtypes.models.ledger.p_finding_classifications import PFindingClassifications
from lx_dtypes.utils.study_setup_yaml import parse_study_setup_yaml


@pytest.fixture(scope="module")
def kb() -> KnowledgeBase:
    descriptor = get_packaged_knowledge_base("coloreg", "0.3.0")
    return DataLoader(
        input_dirs=[descriptor.installed_data_root()]
    ).load_knowledge_base("coloreg")


def test_resection_template_exports_complete_inputs(kb: KnowledgeBase) -> None:
    template = kb.export_report_template("coloreg_colonoscopy")
    assert template["version"] == "2.0.0"
    assert template["readiness"]["can_publish"] is True
    assert template["readiness"]["blocking_issues"] == 0
    assert len(template["report_sections"]) == 3
    assert kb.classification["coloreg_resection_technique"].classification_choices == [
        "coloreg_technique_emr",
        "coloreg_technique_esd",
        "coloreg_technique_eftr",
    ]
    resection = template["report_sections"][1]["findings"][0]
    follow_up = template["report_sections"][2]["findings"][0]
    assert resection["multiple_allowed"] and follow_up["multiple_allowed"]
    assert resection["finding"] == "coloreg_polyp_resection"
    assert follow_up["finding"] == "coloreg_polyp_follow_up"
    assert set(kb.finding["coloreg_polyp_follow_up"].classifications) >= {
        "coloreg_case_id",
        "coloreg_lesion_id",
        "coloreg_index_examination_id",
        "coloreg_index_polyp_finding_id",
        "coloreg_index_resection_finding_id",
        "coloreg_previous_follow_up_examination_id",
        "coloreg_follow_up_sequence",
        "coloreg_follow_up_result",
        "coloreg_interval_bleeding",
        "coloreg_interval_uncontrolled_bleeding",
        "coloreg_interval_perforation",
        "coloreg_repeat_required_bleeding",
        "coloreg_repeat_required_perforation",
        "coloreg_nonpassable_stenosis",
    }


@pytest.mark.parametrize(
    "instrument,requires_settings",
    [
        ("coloreg_snare_cold", False),
        ("coloreg_snare_diathermic", True),
        ("coloreg_snare_both", True),
        ("coloreg_snare_not_used", False),
    ],
)
def test_electricity_requirement_is_conditional_and_lesion_local(
    kb: KnowledgeBase,
    instrument: str,
    requires_settings: bool,
) -> None:
    validator = kb.findings_validator["coloreg_hot_snare_requires_settings"]
    incomplete = {
        "finding": "coloreg_polyp_resection",
        "classifications": {
            "coloreg_snare_type": instrument,
        },
    }
    complete = {
        "finding": "coloreg_polyp_resection",
        "classifications": {
            "coloreg_snare_type": "coloreg_snare_diathermic",
            "coloreg_electrosurgery_settings": "coloreg_electrosurgery_documented",
        },
    }
    # A second lesion with settings cannot satisfy the first lesion's requirement.
    result = evaluate_findings_validator_runtime(
        validator, reported_findings=[incomplete, complete]
    )
    assert result["ok"] is (not requires_settings)
    incomplete["classifications"]["coloreg_electrosurgery_settings"] = (
        "coloreg_electrosurgery_documented"
    )
    assert evaluate_findings_validator_runtime(
        validator, reported_findings=[incomplete]
    )["ok"]


@pytest.mark.parametrize("technique", ["emr", "esd", "eftr"])
def test_technique_requires_corresponding_intervention(
    kb: KnowledgeBase, technique: str
) -> None:
    validator = kb.findings_validator[
        f"coloreg_technique_{technique}_requires_intervention"
    ]
    occurrence = {
        "finding": "coloreg_polyp_resection",
        "classifications": {
            "coloreg_resection_technique": f"coloreg_technique_{technique}",
        },
        "interventions": [],
    }
    assert not evaluate_findings_validator_runtime(
        validator, reported_findings=[occurrence]
    )["ok"]
    occurrence["interventions"] = [f"endoscopy_{technique}_generic"]
    assert evaluate_findings_validator_runtime(
        validator, reported_findings=[occurrence]
    )["ok"]


@pytest.mark.parametrize(
    "outcome,requires_protocol", [("yes", True), ("no", True), ("unknown", False)]
)
def test_primary_success_remains_protocol_defined(
    kb: KnowledgeBase, outcome: str, requires_protocol: bool
) -> None:
    validator = kb.findings_validator["coloreg_primary_success_requires_protocol"]
    occurrence = {
        "finding": "coloreg_polyp_resection",
        "classifications": {
            "coloreg_primary_success": outcome,
            "coloreg_resection_mode": "coloreg_mode_en_bloc",
            "coloreg_histological_margin_status": "coloreg_margin_r0",
        },
    }
    assert evaluate_findings_validator_runtime(
        validator, reported_findings=[occurrence]
    )["ok"] is (not requires_protocol)
    occurrence["classifications"]["coloreg_primary_success_protocol"] = (
        "coloreg_primary_success_protocol_documented"
    )
    assert evaluate_findings_validator_runtime(
        validator, reported_findings=[occurrence]
    )["ok"]


def test_later_follow_up_requires_preceding_visit_on_same_lesion(
    kb: KnowledgeBase,
) -> None:
    validator = kb.findings_validator["coloreg_subsequent_follow_up_requires_previous"]
    first = {
        "finding": "coloreg_polyp_follow_up",
        "classifications": {
            "coloreg_follow_up_sequence": "coloreg_follow_up_first",
        },
    }
    later = {
        "finding": "coloreg_polyp_follow_up",
        "classifications": {
            "coloreg_follow_up_sequence": "coloreg_follow_up_subsequent",
        },
    }
    assert evaluate_findings_validator_runtime(validator, reported_findings=[first])[
        "ok"
    ]
    assert not evaluate_findings_validator_runtime(
        validator, reported_findings=[first, later]
    )["ok"]
    later["classifications"]["coloreg_previous_follow_up_examination_id"] = (
        "coloreg_previous_follow_up_examination_id_documented"
    )
    assert evaluate_findings_validator_runtime(
        validator, reported_findings=[first, later]
    )["ok"]


def electricity_exam(kb: KnowledgeBase, settings: str) -> PExamination:
    """Synthetic ledger observation: a choice alone does not supply its input values."""
    exam = PExamination(
        examination="colonoscopy",
        patient=str(uuid5(NAMESPACE_URL, "coloreg-synthetic-patient")),
        uuid=uuid5(NAMESPACE_URL, "coloreg-test-exam"),
    )
    finding = PFinding(
        finding="coloreg_polyp_resection", patient_examination=str(exam.uuid)
    )
    group = PFindingClassifications(patient_finding=str(finding.uuid))
    choice = PFindingClassificationChoice(
        classification="coloreg_electrosurgery_settings",
        classification_choice="coloreg_electrosurgery_documented",
        patient_finding_classifications=str(group.uuid),
    )
    names = kb.classification_choice[
        "coloreg_electrosurgery_documented"
    ].classification_choice_descriptors
    for name, value in zip(
        names, ["Synthetic generator", "Synthetic mode", settings], strict=True
    ):
        choice.patient_finding_classification_choice_descriptors.append(
            PFindingClassificationChoiceDescriptor(
                classification_choice_descriptor=name,
                descriptor_value=value,
                patient_finding_classification_choice=str(choice.uuid),
            )
        )
    group.patient_finding_classification_choices.append(choice)
    finding.patient_finding_classifications.append(group)
    exam.patient_findings.append(finding)
    return exam


@pytest.mark.parametrize(
    "settings,expected",
    [("", "invalid"), ("Effect 2; cut interval 3; power not exposed", "present")],
)
def test_coverage_checks_actual_electricity_settings(
    kb: KnowledgeBase, settings: str, expected: str
) -> None:
    exam = electricity_exam(kb, settings)
    kb.assert_examination_admissibility(exam, template_name="coloreg_colonoscopy")
    coverage = build_report_concept_coverage(
        kb=kb,
        requested_template_name="coloreg_colonoscopy",
        template_export=kb.export_report_template("coloreg_colonoscopy"),
        p_examination=exam,
        validation={},
    )
    item = next(
        c
        for c in coverage.concepts
        if c.concept_id == "coloreg_polyp_resection.coloreg_electrosurgery_settings.2"
    )
    assert item.validation_status == expected


def test_study_hypotheses_pin_terminology_and_do_not_claim_automatic_analysis(
    kb: KnowledgeBase,
) -> None:
    root = package_data_root()
    study = parse_study_setup_yaml(
        (root / "study_metadata/coloreg_resection.yml").read_text()
    )
    assert len(study.cohorts) == 4
    for cohort in study.cohorts:
        assert "H0:" in cohort.hypothesis and "H1:" in cohort.hypothesis
        assert ">= 20 mm" in cohort.hypothesis
        assert "gleich" in cohort.hypothesis
        assert [
            (r.module, r.version)
            for r in cohort.study_metadata.terminology_requirements
        ] == [("coloreg", "0.3.0")]
        for criterion in cohort.study_metadata.inclusion_criteria:
            assert "not executable cohort filters" in criterion.description
            for concept in criterion.concepts:
                assert concept.name in kb.finding
    spec = yaml.safe_load(
        (
            Path(__file__).resolve().parents[3]
            / "docs/guides/coloreg-resection-study.yml"
        ).read_text()
    )
    assert spec["population"]["size"]["minimum_inclusive"] == 20
    assert spec["endpoints"]["primary_success"]["definition"].startswith(
        "Protocol-defined"
    )
    assert "not_performed" in " ".join(
        kb.classification["coloreg_follow_up_result"].classification_choices
    )
    assert (
        "coloreg_margin_rx"
        in kb.classification[
            "coloreg_histological_margin_status"
        ].classification_choices
    )


def test_previous_release_retains_its_digest_and_template() -> None:
    old = get_packaged_knowledge_base("coloreg", "0.2.0")
    assert (
        old.content_sha256
        == "e3c8444570369fa4af50ed307d290ba588a606584b30bae31bbf9fc2157d9838"
    )
    old_kb = DataLoader(input_dirs=[old.installed_data_root()]).load_knowledge_base(
        "coloreg"
    )
    assert old_kb.report_template["coloreg_colonoscopy"].version == "1.0.0"
    assert "coloreg_polyp_resection" not in old_kb.finding
    assert get_packaged_knowledge_base("coloreg").version == "0.3.0"


@pytest.mark.parametrize(
    "source,target",
    [
        ("coloreg_interval_uncontrolled_bleeding", "coloreg_interval_bleeding"),
        ("coloreg_repeat_required_bleeding", "coloreg_interval_bleeding"),
        ("coloreg_repeat_required_perforation", "coloreg_interval_perforation"),
    ],
)
def test_complication_trigger_requires_positive_event_on_same_lesion(
    kb: KnowledgeBase,
    source: str,
    target: str,
) -> None:
    rule = kb.findings_validator[source + "_requires_event"]
    occurrence = {
        "finding": "coloreg_polyp_follow_up",
        "classifications": {source: "yes", target: "no"},
    }
    other_lesion = {
        "finding": "coloreg_polyp_follow_up",
        "classifications": {source: "yes", target: "yes"},
    }
    assert not evaluate_findings_validator_runtime(
        rule, reported_findings=[occurrence, other_lesion]
    )["ok"]
    occurrence["classifications"][target] = "yes"
    assert evaluate_findings_validator_runtime(rule, reported_findings=[occurrence])[
        "ok"
    ]
