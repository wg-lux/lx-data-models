"""Medication and electrosurgery are evaluable in a colonoscopy report template."""

from __future__ import annotations

from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

import pytest

from lx_dtypes.knowledge_bases import (
    get_packaged_knowledge_base,
    knowledge_base_content_sha256,
)
from lx_dtypes.models.interface.KnowledgeBase import (
    KnowledgeBase,
    SemanticAdmissibilityError,
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
from lx_dtypes.packages import validate_package
from lx_dtypes.validation import assess_examination
from tests.paths import PACKAGE_ROOT, REPOSITORY_ROOT

TEMPLATE = "colonoscopy_medication_electrosurgery"
MANIFEST = REPOSITORY_ROOT / "docs/examples/dtypes_packages" / TEMPLATE / "config.yaml"
# (classification, choice, descriptor values in the choice's declared order)
Selection = tuple[str, str, list[float | str]]

MEDICATION: list[Selection] = [
    ("endoscopy_medication_product_and_dose", "medication_propofol", [120.0]),
    ("medication_administration_route", "medication_route_intravenous", []),
    ("medication_administration_method", "medication_method_bolus", []),
    (
        "medication_administration_time",
        "medication_administration_time_recorded",
        ["10:42"],
    ),
]
ELECTROSURGERY: list[Selection] = [
    ("electrosurgery_mode", "electrosurgery_mode_cut", []),
    ("electrosurgery_power_setting", "electrosurgery_power_setting_recorded", [40.0]),
    (
        "electrosurgery_activation_duration",
        "electrosurgery_activation_duration_recorded",
        [1.8],
    ),
    (
        "electrosurgery_delivered_energy",
        "electrosurgery_delivered_energy_recorded",
        [62.5],
    ),
    (
        "electrosurgery_curve_comparison",
        "electrosurgery_curve_within_reference",
        [2.1],
    ),
]
STATUS: dict[str, list[Selection]] = {
    "endoscopy_medication_status": [
        ("endoscopy_medication_documentation_status", "documented_present", [])
    ],
    "endoscopy_electrosurgery_status": [
        ("endoscopy_electrosurgery_documentation_status", "documented_present", [])
    ],
}


@pytest.fixture(scope="module")
def kb() -> KnowledgeBase:
    data = PACKAGE_ROOT / "data"
    # Current packages only: retained releases under versions/ are other identities.
    current = [
        path
        for path in sorted((data / "terminology").iterdir())
        if path.is_dir() and path.name != "versions"
    ]
    result = validate_package(
        MANIFEST,
        input_dirs=[
            *current,
            data / "report_templates" / "report_medications",
            data / "report_templates" / "report_electrosurgery",
            MANIFEST.parent,
        ],
        language="en",
    )
    assert result.ok, result.issues
    assert result.knowledge_base is not None
    return result.knowledge_base


def _finding(
    kb: KnowledgeBase, exam: PExamination, name: str, selections: list[Selection]
) -> None:
    finding = PFinding(finding=name, patient_examination=str(exam.uuid))
    for classification, choice_name, values in selections:
        group = PFindingClassifications(patient_finding=str(finding.uuid))
        choice = PFindingClassificationChoice(
            classification=classification,
            classification_choice=choice_name,
            patient_finding_classifications=str(group.uuid),
        )
        descriptors = kb.classification_choice[
            choice_name
        ].classification_choice_descriptors
        for descriptor, value in zip(descriptors, values, strict=True):
            choice.patient_finding_classification_choice_descriptors.append(
                PFindingClassificationChoiceDescriptor(
                    classification_choice_descriptor=descriptor,
                    descriptor_value=value,
                    patient_finding_classification_choice=str(choice.uuid),
                )
            )
        group.patient_finding_classification_choices.append(choice)
        finding.patient_finding_classifications.append(group)
    exam.patient_findings.append(finding)


def _examination(
    kb: KnowledgeBase,
    *,
    electrosurgery: list[Selection] | None = None,
    with_status: bool = True,
) -> PExamination:
    exam = PExamination(
        examination="colonoscopy",
        patient=str(uuid5(NAMESPACE_URL, "synthetic-patient")),
        uuid=uuid5(NAMESPACE_URL, "synthetic-exam"),
        **kb.config.knowledge_base_identity.model_dump(),
    )
    if with_status:
        for name, selections in STATUS.items():
            _finding(kb, exam, name, selections)
    _finding(kb, exam, "endoscopy_medication_administration", MEDICATION)
    _finding(
        kb,
        exam,
        "endoscopy_electrosurgery_application",
        ELECTROSURGERY if electrosurgery is None else electrosurgery,
    )
    return exam


def test_template_exposes_both_sections_in_shell_hierarchy(kb: KnowledgeBase) -> None:
    exported = kb.export_report_template(TEMPLATE)

    assert exported["readiness"]["can_publish"]
    assert exported["readiness"]["issues"] == []
    sections = {section["name"]: section for section in exported["report_sections"]}
    assert sections["report_medications"]["section_kind"] == "medications"
    assert sections["report_electrosurgery"]["section_kind"] == "findings"
    application = next(
        finding
        for finding in sections["report_electrosurgery"]["findings"]
        if finding["finding"] == "endoscopy_electrosurgery_application"
    )
    assert application["multiple_allowed"] and not application["required"]
    assert {
        item["classification"]: item["required"]
        for item in application["classifications"]
    } == {
        "electrosurgery_mode": True,
        "electrosurgery_power_setting": True,
        "electrosurgery_activation_duration": False,
        "electrosurgery_delivered_energy": False,
        "electrosurgery_curve_comparison": False,
    }
    # Every numeric detail value carries an explicit unit.
    for name in (
        "electrosurgery_power_setting_watt_value",
        "electrosurgery_activation_duration_seconds_value",
        "electrosurgery_delivered_energy_joule_value",
        "electrosurgery_curve_distance_value",
        "propofol_dose_mg_value",
    ):
        descriptor = kb.classification_choice_descriptor[name]
        assert descriptor.unit in kb.unit and descriptor.unit != "unknown", name


def test_documented_examination_passes_and_missing_status_fails(
    kb: KnowledgeBase,
) -> None:
    complete = _examination(kb)
    kb.assert_examination_admissibility(complete, template_name=TEMPLATE)
    passed = assess_examination(kb, complete, template_name=TEMPLATE, language="en")
    assert passed.study_evaluated
    assert passed.ok, passed.issues

    missing = assess_examination(
        kb, _examination(kb, with_status=False), template_name=TEMPLATE, language="en"
    )
    assert not missing.ok
    assert {issue.code for issue in missing.issues if issue.level == "error"} == {
        "finding_not_present",
        "failed_finding_validator_dependency",
    }
    messages = " ".join(issue.message for issue in missing.issues)
    assert kb.finding["endoscopy_medication_status"].name_en in messages
    assert "endoscopy_medication_status" not in messages
    assert kb.finding["endoscopy_electrosurgery_status"].name_en in messages
    assert "endoscopy_electrosurgery_status" not in messages


def test_incomplete_application_is_reported(kb: KnowledgeBase) -> None:
    without_power = [
        item for item in ELECTROSURGERY if item[0] != "electrosurgery_power_setting"
    ]
    runtime = kb.evaluate_report_template_validators(
        TEMPLATE, p_examination=_examination(kb, electrosurgery=without_power)
    )
    by_name = {item["name"]: item for item in runtime["classification_validators"]}

    assert by_name["elektrochirurgie_modus_vollstaendig"]["ok"]
    assert not by_name["elektrochirurgie_leistung_vollstaendig"]["ok"]


@pytest.mark.parametrize(
    "selection",
    [
        (
            "electrosurgery_power_setting",
            "electrosurgery_power_setting_recorded",
            [900.0],
        ),
        ("electrosurgery_mode", "medication_propofol", [120.0]),
    ],
)
def test_implausible_or_foreign_values_are_inadmissible(
    kb: KnowledgeBase, selection: Selection
) -> None:
    exam = _examination(kb, electrosurgery=[selection])
    with pytest.raises(SemanticAdmissibilityError):
        kb.assert_examination_admissibility(exam, template_name=TEMPLATE)


def test_shared_section_package_is_catalogued() -> None:
    packaged = get_packaged_knowledge_base("report_electrosurgery", "0.1.0")
    assert (
        knowledge_base_content_sha256(packaged.resource_directory())
        == packaged.content_sha256
    )
    assert Path(packaged.resource_root).name == "report_electrosurgery"


def _medication_method_ok(kb: KnowledgeBase, choice: str) -> bool:
    exam = _examination(kb)
    administration = next(
        finding
        for finding in exam.patient_findings
        if finding.finding == "endoscopy_medication_administration"
    )
    for group in administration.patient_finding_classifications:
        for selected in group.patient_finding_classification_choices:
            if selected.classification == "medication_administration_method":
                selected.classification_choice = choice
    runtime = kb.evaluate_report_template_validators(TEMPLATE, p_examination=exam)
    return all(
        result["ok"]
        for result in runtime["classification_validators"]
        if result["classification"] == "medication_administration_method"
    )


def test_descriptor_free_choice_completes_a_mixed_classification(
    kb: KnowledgeBase,
) -> None:
    # Bolus declares no input; infusion requires its actual flow rate.
    assert _medication_method_ok(kb, "medication_method_bolus")
    assert not _medication_method_ok(kb, "medication_method_infusion")


def test_electrosurgery_status_is_optional_in_the_dgvs_template() -> None:
    from lx_dtypes.models.interface.DataLoader import DataLoader

    kb = DataLoader(input_dirs=[PACKAGE_ROOT / "data"]).load_knowledge_base(
        "dgvs_reporting"
    )
    exported = kb.export_report_template("colonoscopy_training_basic")
    section = next(
        s for s in exported["report_sections"] if s["name"] == "report_electrosurgery"
    )
    status = next(
        f
        for f in section["findings"]
        if f["finding"] == "endoscopy_electrosurgery_status"
    )
    assert status["required"] is False
    # When documented, the status still needs its value.
    assert [c["required"] for c in status["classifications"]] == [True]
    assert "elektrochirurgie_status_dokumentiert" not in (
        kb.report_template[
            "colonoscopy_training_basic"
        ].validators.examination_validators
    )


def test_german_missing_status_messages_use_display_labels(kb: KnowledgeBase) -> None:
    report = assess_examination(
        kb,
        _examination(kb, with_status=False),
        template_name=TEMPLATE,
    )
    messages = " ".join(issue.message for issue in report.issues)
    assert kb.finding["endoscopy_medication_status"].name_de in messages
    assert kb.finding["endoscopy_electrosurgery_status"].name_de in messages
    assert "endoscopy_medication_status" not in messages
    assert "example_medication_status_documented" not in messages
