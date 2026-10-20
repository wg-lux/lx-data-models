"""Explicit, authorization-neutral ColoReg lesion linkage for descriptive analysis."""

from __future__ import annotations

from collections.abc import Sequence

from lx_dtypes.models.contracts.study_analysis import (
    StudyAnalysisUnit,
    StudyFindingReference,
)
from lx_dtypes.models.ledger.p_examination.Pydantic import PExamination
from lx_dtypes.models.ledger.p_finding.Pydantic import PFinding
from lx_dtypes.models.ledger.p_finding_classification_choice.Pydantic import (
    PFindingClassificationChoice,
)

_CASE = "coloreg_case_id"
_LESION = "coloreg_lesion_id"
_EXAM = "coloreg_index_examination_id"
_POLYP = "coloreg_index_polyp_finding_id"
_RESECTION = "coloreg_index_resection_finding_id"
_PREVIOUS = "coloreg_previous_follow_up_examination_id"


def latest_study_choices(finding: PFinding) -> list[PFindingClassificationChoice]:
    """Read latest ledger classification revision without mutating empty findings.

    Equal newest timestamps are contradictory revision provenance and rejected.
    """
    groups = finding.patient_finding_classifications
    if not groups:
        return []
    newest = max(group.created_at for group in groups)
    matches = [group for group in groups if group.created_at == newest]
    if len(matches) != 1:
        raise ValueError("Ambiguous latest finding classifications")
    return matches[0].patient_finding_classification_choices


def _value(
    finding: PFinding, classification: str, descriptor: str | None = None
) -> str | float | None:
    choices = [
        choice
        for choice in latest_study_choices(finding)
        if choice.classification == classification
    ]
    if len(choices) > 1:
        raise ValueError(f"Ambiguous linkage classification: {classification}")
    if not choices:
        return None
    if descriptor is None:
        return choices[0].classification_choice
    values = [
        item.descriptor_value
        for item in choices[0].patient_finding_classification_choice_descriptors
        if item.classification_choice_descriptor == descriptor
    ]
    if len(values) > 1:
        raise ValueError(f"Ambiguous linkage descriptor: {descriptor}")
    if not values or values[0] is None:
        return None
    value = values[0]
    if isinstance(value, bool) or not isinstance(value, (str, float, int)):
        raise ValueError(f"Invalid linkage descriptor: {descriptor}")  # noqa: TRY004 - Invalid ledger data, consistent with other linkage failures.
    return value if isinstance(value, str) else float(value)


def _link(finding: PFinding, classification: str) -> str | None:
    value = _value(finding, classification, classification + "_value")
    if value is not None and (not isinstance(value, str) or not value.strip()):
        raise ValueError(f"Invalid linkage identifier: {classification}")
    return value


def _ref(record: PExamination, finding: PFinding) -> StudyFindingReference:
    return StudyFindingReference(
        record_uuid=str(record.uuid), finding_uuid=str(finding.uuid)
    )


def assemble_coloreg_analysis_units(
    records: Sequence[PExamination],
) -> list[StudyAnalysisUnit]:
    """Assemble one unit per attempted resection from already authorized records.

    Identifiers refer to canonical ledger UUIDs, never examination names. Missing
    links remain missing roles. Contradictory links fail closed. The longitudinal
    role uses the first unremarkable visit and its next explicitly chained,
    evaluable visit (abnormal and unremarkable both qualify). Missing timestamps
    cannot establish order. Hosts must scope records before calling this function.
    """
    by_record = {str(record.uuid): record for record in records}
    if len(by_record) != len(records):
        raise ValueError("Duplicate examination UUID")
    findings: dict[str, tuple[PExamination, PFinding]] = {}
    for record in records:
        for finding in record.patient_findings:
            if str(finding.uuid) in findings:
                raise ValueError("Duplicate finding UUID")
            findings[str(finding.uuid)] = record, finding
    units: list[StudyAnalysisUnit] = []
    lesions: set[tuple[str, str, str]] = set()
    for record in records:
        for index in record.patient_findings:
            if index.finding != "coloreg_polyp_resection":
                continue
            unit = StudyAnalysisUnit(index=_ref(record, index))
            units.append(unit)
            case, lesion, exam, polyp_id = (
                _link(index, key) for key in (_CASE, _LESION, _EXAM, _POLYP)
            )
            if exam is not None and exam != str(record.uuid):
                raise ValueError("Index examination link contradicts resection record")
            if case and lesion:
                key = record.patient, case, lesion
                if key in lesions:
                    raise ValueError("Duplicate index resection for case/lesion")
                lesions.add(key)
            if polyp_id in findings:
                polyp_record, polyp = findings[polyp_id]
                if (
                    polyp_record.patient != record.patient
                    or polyp_record.uuid != record.uuid
                    or polyp.finding != "colon_polyp"
                ):
                    raise ValueError(
                        "Index polyp must belong to the same examination and patient"
                    )
                original_size = _value(polyp, "lesion_size_mm", "lesion_size_mm_value")
                copied_size = _value(index, "lesion_size_mm", "lesion_size_mm_value")
                if (
                    copied_size is not None
                    and original_size is not None
                    and copied_size != original_size
                ):
                    raise ValueError("Index polyp and resection size discrepancy")
                if all((case, lesion, exam, polyp_id)):
                    unit.polyp = _ref(polyp_record, polyp)
            visits: dict[str, tuple[PExamination, PFinding]] = {}
            for visit_record, visit in findings.values():
                if visit.finding != "coloreg_polyp_follow_up" or _link(
                    visit, _RESECTION
                ) != str(index.uuid):
                    continue
                if visit_record.patient != record.patient:
                    raise ValueError("Follow-up references another patient")
                if _link(visit, _PREVIOUS) == str(visit_record.uuid):
                    raise ValueError("Follow-up cannot reference itself")
                values = tuple(
                    _link(visit, key) for key in (_CASE, _LESION, _EXAM, _POLYP)
                )
                expected = (case, lesion, exam, polyp_id)
                if any(
                    actual is not None and target is not None and actual != target
                    for actual, target in zip(values, expected)
                ):
                    raise ValueError("Follow-up contradicts index lesion linkage")
                if visit_record.uuid == record.uuid:
                    raise ValueError("Follow-up cannot be the index examination")
                if (
                    visit_record.date is not None
                    and record.date is not None
                    and visit_record.date <= record.date
                ):
                    raise ValueError("Follow-up must occur after index examination")
                if str(visit_record.uuid) in visits:
                    raise ValueError("Duplicate lesion follow-up within examination")
                if all(values) and all(expected):
                    visits[str(visit_record.uuid)] = visit_record, visit
            # Check every explicit predecessor, including unavailable-role chains.
            for visit_id, (visit_record, visit) in visits.items():
                predecessor = _link(visit, _PREVIOUS)
                seen = {visit_id}
                while predecessor in visits:
                    if predecessor in seen:
                        raise ValueError("Follow-up linkage cycle")
                    seen.add(predecessor)
                    predecessor = _link(visits[predecessor][1], _PREVIOUS)
                previous_id = _link(visit, _PREVIOUS)
                if (
                    previous_id in by_record
                    and by_record[previous_id].patient != record.patient
                ):
                    raise ValueError("Previous follow-up references another patient")
                if previous_id in by_record and previous_id not in visits:
                    candidates = [
                        candidate
                        for candidate in by_record[previous_id].patient_findings
                        if candidate.finding == "coloreg_polyp_follow_up"
                    ]
                    expected_links = (case, lesion, exam, polyp_id, str(index.uuid))
                    if candidates and all(
                        any(
                            actual is not None
                            and target is not None
                            and actual != target
                            for actual, target in zip(
                                (
                                    _link(candidate, key)
                                    for key in (
                                        _CASE,
                                        _LESION,
                                        _EXAM,
                                        _POLYP,
                                        _RESECTION,
                                    )
                                ),
                                expected_links,
                            )
                        )
                        for candidate in candidates
                    ):
                        raise ValueError(
                            "Previous follow-up contradicts index lesion linkage"
                        )
                if previous_id in visits:
                    previous_record = visits[previous_id][0]
                    if (
                        previous_record.date is not None
                        and visit_record.date is not None
                        and previous_record.date >= visit_record.date
                    ):
                        raise ValueError(
                            "Previous follow-up must precede current examination"
                        )
            dated = sorted(
                (pair for pair in visits.values() if pair[0].date is not None),
                key=lambda pair: pair[0].date.timestamp() if pair[0].date else 0,
            )
            if len({pair[0].date for pair in dated}) != len(dated):
                raise ValueError("Ambiguous follow-up examination timestamps")
            if record.date is None:
                continue
            for previous_record, previous in dated:
                if (
                    _value(previous, "coloreg_follow_up_result")
                    != "coloreg_follow_up_unremarkable"
                ):
                    continue
                unit.previous_follow_up = _ref(previous_record, previous)
                for current_record, current in dated:
                    if (
                        current_record.date is None
                        or previous_record.date is None
                        or current_record.date <= previous_record.date
                    ):
                        continue
                    predecessor = _link(current, _PREVIOUS)
                    while predecessor in visits and predecessor != str(
                        previous_record.uuid
                    ):
                        intermediate_record, intermediate = visits[predecessor]
                        if intermediate_record.date is None or _value(
                            intermediate, "coloreg_follow_up_result"
                        ) in {
                            "coloreg_follow_up_unremarkable",
                            "coloreg_follow_up_abnormal",
                        }:
                            break
                        predecessor = _link(intermediate, _PREVIOUS)
                    if predecessor == str(previous_record.uuid) and _value(
                        current, "coloreg_follow_up_result"
                    ) in {
                        "coloreg_follow_up_unremarkable",
                        "coloreg_follow_up_abnormal",
                    }:
                        unit.previous_follow_up = _ref(previous_record, previous)
                        unit.follow_up = _ref(current_record, current)
                        break
                # Do not move the conditioning baseline to a later visit merely
                # because its outcome is more completely observed.
                break
    return units
