from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from lx_dtypes.models.ledger.p_examination.Pydantic import PExamination
from lx_dtypes.models.ledger.p_finding.Pydantic import PFinding
from lx_dtypes.models.ledger.p_finding_classification_choice.Pydantic import (
    PFindingClassificationChoice,
)
from lx_dtypes.models.ledger.p_finding_classification_choice_descriptor.Pydantic import (
    PFindingClassificationChoiceDescriptor,
)
from lx_dtypes.models.ledger.p_finding_classifications.Pydantic import (
    PFindingClassifications,
)
from lx_dtypes.stats.study_linkage import assemble_coloreg_analysis_units


def _set(
    finding: PFinding, key: str, value: str | float, *, choice: bool = False
) -> None:
    if not finding.patient_finding_classifications:
        finding.patient_finding_classifications.append(
            PFindingClassifications(patient_finding=str(finding.uuid))
        )
    group = finding.patient_finding_classifications[0]
    group.patient_finding_classification_choices[:] = [
        item
        for item in group.patient_finding_classification_choices
        if item.classification != key
    ]
    item = PFindingClassificationChoice(
        classification=key,
        classification_choice=str(value) if choice else key + "_documented",
        patient_finding_classifications=str(group.uuid),
    )
    if not choice:
        item.patient_finding_classification_choice_descriptors.append(
            PFindingClassificationChoiceDescriptor(
                classification_choice_descriptor=key + "_value",
                descriptor_value=value,
                patient_finding_classification_choice=str(item.uuid),
            )
        )
    group.patient_finding_classification_choices.append(item)


def _dataset() -> list[PExamination]:
    index_record = PExamination(
        patient="synthetic-patient",
        examination="colonoscopy",
        date=datetime(2025, 1, 1, tzinfo=UTC),
    )
    polyp = PFinding(finding="colon_polyp", patient_examination="colonoscopy")
    index = PFinding(
        finding="coloreg_polyp_resection", patient_examination="colonoscopy"
    )
    index_record.patient_findings = [polyp, index]
    links = {
        "coloreg_case_id": "case",
        "coloreg_lesion_id": "lesion",
        "coloreg_index_examination_id": str(index_record.uuid),
        "coloreg_index_polyp_finding_id": str(polyp.uuid),
    }
    for key, value in links.items():
        _set(index, key, value)
    _set(polyp, "lesion_size_mm", 25.0)
    _set(index, "lesion_size_mm", 25.0)
    records = [index_record]
    for offset, result in [(1, "unremarkable"), (2, "abnormal"), (3, "unremarkable")]:
        record = PExamination(
            patient="synthetic-patient",
            examination="colonoscopy",
            date=datetime(2025, 1, 1, tzinfo=UTC) + timedelta(days=offset),
        )
        finding = PFinding(
            finding="coloreg_polyp_follow_up", patient_examination="colonoscopy"
        )
        for key, value in links.items():
            _set(finding, key, value)
        _set(finding, "coloreg_index_resection_finding_id", str(index.uuid))
        _set(
            finding,
            "coloreg_follow_up_result",
            "coloreg_follow_up_" + result,
            choice=True,
        )
        if offset > 1:
            _set(
                finding,
                "coloreg_previous_follow_up_examination_id",
                str(records[-1].uuid),
            )
        record.patient_findings.append(finding)
        records.append(record)
    return records


def test_explicit_roles_keep_first_abnormal_outcome_and_ignore_input_order():
    records = _dataset()
    (unit,) = assemble_coloreg_analysis_units(list(reversed(records)))
    assert unit.polyp is not None
    assert (
        unit.previous_follow_up is not None
        and unit.previous_follow_up.record_uuid == str(records[1].uuid)
    )
    assert unit.follow_up is not None and unit.follow_up.record_uuid == str(
        records[2].uuid
    )


def test_unavailable_link_and_dates_remain_unknown():
    records = _dataset()
    _set(records[0].patient_findings[1], "coloreg_index_polyp_finding_id", str(uuid4()))
    (unit,) = assemble_coloreg_analysis_units(records[:1])
    assert unit.polyp is None
    assert unit.follow_up is None
    records = _dataset()
    records[1].date = None
    (unit,) = assemble_coloreg_analysis_units(records[:3])
    assert unit.follow_up is None


@pytest.mark.parametrize(
    "mutation", ["patient", "size", "cycle", "order", "duplicate", "lesion"]
)
def test_rejects_contradictory_linkage(mutation: str):
    records = _dataset()
    if mutation == "patient":
        records[2].patient = "another-patient"
    elif mutation == "size":
        _set(records[0].patient_findings[1], "lesion_size_mm", 30.0)
    elif mutation == "cycle":
        _set(
            records[1].patient_findings[0],
            "coloreg_previous_follow_up_examination_id",
            str(records[2].uuid),
        )
    elif mutation == "order":
        records[2].date = records[1].date
    elif mutation == "duplicate":
        records.append(records[0])
    else:
        _set(records[1].patient_findings[0], "coloreg_lesion_id", "different-lesion")
    with pytest.raises(ValueError):
        assemble_coloreg_analysis_units(records)


def test_unevaluable_intermediate_visit_can_be_skipped_without_positive_selection():
    records = _dataset()
    _set(
        records[2].patient_findings[0],
        "coloreg_follow_up_result",
        "coloreg_follow_up_not_assessable",
        choice=True,
    )
    _set(
        records[3].patient_findings[0],
        "coloreg_follow_up_result",
        "coloreg_follow_up_abnormal",
        choice=True,
    )
    (unit,) = assemble_coloreg_analysis_units(records)
    assert unit.follow_up is not None and unit.follow_up.record_uuid == str(
        records[3].uuid
    )


def test_missing_successor_does_not_move_conditioning_baseline():
    records = _dataset()
    _set(
        records[2].patient_findings[0],
        "coloreg_previous_follow_up_examination_id",
        str(uuid4()),
    )
    (unit,) = assemble_coloreg_analysis_units(records)
    assert unit.previous_follow_up is not None
    assert unit.previous_follow_up.record_uuid == str(records[1].uuid)
    assert unit.follow_up is None


def test_ambiguous_visit_dates_are_rejected():
    records = _dataset()
    records[3].date = records[2].date
    _set(
        records[3].patient_findings[0],
        "coloreg_previous_follow_up_examination_id",
        str(records[1].uuid),
    )
    with pytest.raises(ValueError, match="timestamps"):
        assemble_coloreg_analysis_units(records)


def test_authorized_previous_examination_with_only_other_lesion_is_rejected():
    records = _dataset()
    _set(
        records[1].patient_findings[0],
        "coloreg_index_resection_finding_id",
        str(uuid4()),
    )
    _set(records[1].patient_findings[0], "coloreg_lesion_id", "another-lesion")
    with pytest.raises(ValueError, match="Previous follow-up contradicts"):
        assemble_coloreg_analysis_units(records)


def test_authorized_previous_without_followup_data_remains_unknown():
    records = _dataset()
    records[1].patient_findings = []
    (unit,) = assemble_coloreg_analysis_units(records[:3])
    assert unit.previous_follow_up is None
    assert unit.follow_up is None


def test_latest_classification_revision_is_shared_and_ties_rejected():
    from lx_dtypes.stats.study_linkage import latest_study_choices

    finding = PFinding(finding="colon_polyp", patient_examination="colonoscopy")
    assert latest_study_choices(finding) == []
    assert finding.patient_finding_classifications == []
    _set(finding, "lesion_size_mm", 25.0)
    original = finding.patient_finding_classifications[0]
    original.created_at = datetime(2025, 1, 1, tzinfo=UTC)
    latest = original.model_copy(deep=True)
    latest.created_at += timedelta(days=1)
    latest.patient_finding_classification_choices = []
    finding.patient_finding_classifications.append(latest)
    assert latest_study_choices(finding) == []
    latest.created_at = original.created_at
    with pytest.raises(ValueError, match="Ambiguous latest"):
        latest_study_choices(finding)
