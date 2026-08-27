from __future__ import annotations

import math

import pytest
from pydantic import ValidationError

from lx_dtypes.models.contracts.patient_examination_report import (
    PatientExaminationReportMakeReportPayload,
    PatientExaminationReportSubmissionPayload,
    ReportPersistedArtifactsPayload,
    dump_make_report_payload,
    dump_persisted_artifacts_payload,
    dump_report_submission_payload,
)
from lx_dtypes.models.contracts.report_draft import (
    PatientExaminationReportDraft,
    dump_patient_examination_report_draft,
)


def test_draft_arranges_complete_identity_and_asserts_canonical_persisted_shape() -> (
    None
):
    # Arrange
    draft = {
        "revision": 7,
        "module_name": " clinical_reporting ",
        "template_name": " colonoscopy ",
        "template_identity": {
            "moduleName": " clinical_reporting ",
            "knowledgeBaseVersion": " 2.0.0 ",
            "templateVersion": " 4 ",
            "templateHash": " sha256:template ",
            "lifecycleStatus": " published ",
        },
        "selected_report_language": "de",
        "payload": {"examination": "colonoscopy"},
    }

    # Act
    persisted = dump_patient_examination_report_draft(draft)

    # Assert
    assert persisted["revision"] == 7
    assert persisted["module_name"] == "clinical_reporting"
    assert persisted["template_name"] == "colonoscopy"
    assert persisted["template_identity"] == {
        "module_name": "clinical_reporting",
        "knowledge_base_version": "2.0.0",
        "template_version": "4",
        "template_hash": "sha256:template",
        "lifecycle_status": "published",
    }


@pytest.mark.parametrize(
    "invalid_draft",
    [
        {"revision": True, "payload": {}},
        {"template_identity": {"module_name": 7}, "payload": {}},
        {"template_identity": {"unexpected": "value"}, "payload": {}},
        {"indications": [{"examination_indication_id": 0}], "payload": {}},
        {"template_section_drafts": {"findings": {"include_patient_data": 1}}},
        {"payload": {"non_finite": math.nan}},
    ],
)
def test_draft_arranges_invalid_persisted_value_and_asserts_fail_closed(
    invalid_draft: dict[str, object],
) -> None:
    # Arrange
    payload = invalid_draft

    # Act
    def validate() -> PatientExaminationReportDraft:
        return PatientExaminationReportDraft.model_validate(payload)

    # Assert
    with pytest.raises(ValidationError):
        validate()


def test_final_submission_arranges_versioned_identity_and_asserts_typed_dump() -> None:
    # Arrange
    raw = {
        "report_id": 88,
        "patient_examination_id": 314,
        "template_name": " colonoscopy ",
        "knowledge_base_module": " clinical_reporting ",
        "knowledge_base_version": " 2.0.0 ",
        "template_version": "4",
        "template_hash": "sha256:template",
        "status": "final",
        "expected_version": 3,
        "rendered_text": "Normalbefund.",
    }

    # Act
    payload = PatientExaminationReportSubmissionPayload.model_validate(raw)
    persisted = dump_report_submission_payload(payload)

    # Assert
    assert persisted["status"] == "final"
    assert persisted.get("report_id") == 88
    assert persisted.get("expected_version") == 3
    assert persisted["knowledge_base_module"] == "clinical_reporting"
    assert persisted["knowledge_base_version"] == "2.0.0"


@pytest.mark.parametrize(
    "field,value",
    [
        ("patient_examination_id", 0),
        ("report_id", 0),
        ("expected_version", 0),
        ("status", "validated"),
        ("knowledge_base_module", "clinical@reporting"),
        ("knowledge_base_version", "2@latest"),
    ],
)
def test_final_submission_arranges_invalid_boundary_and_asserts_rejection(
    field: str,
    value: object,
) -> None:
    # Arrange
    raw: dict[str, object] = {
        "report_id": 88,
        "patient_examination_id": 314,
        "template_name": "colonoscopy",
        "knowledge_base_module": "clinical_reporting",
        "knowledge_base_version": "2.0.0",
        "status": "final",
        "expected_version": 3,
        field: value,
    }

    # Act
    def validate() -> PatientExaminationReportSubmissionPayload:
        return PatientExaminationReportSubmissionPayload.model_validate(raw)

    # Assert
    with pytest.raises(ValidationError):
        validate()


@pytest.mark.parametrize("max_frames", [1, 12, 24])
def test_make_report_arranges_supported_frame_limit_and_asserts_exact_dump(
    max_frames: int,
) -> None:
    # Arrange
    raw = {
        "patient_examination_id": 314,
        "report_id": 88,
        "knowledge_base_module": "clinical_reporting",
        "knowledge_base_version": "2.0.0",
        "patient": {
            "first_name": "Ada",
            "last_name": "Lovelace",
            "dob": "1815-12-10",
        },
        "max_frames": max_frames,
    }

    # Act
    payload = PatientExaminationReportMakeReportPayload.model_validate(raw)
    result = dump_make_report_payload(payload)

    # Assert
    assert result["patient_examination_id"] == 314
    assert result.get("report_id") == 88
    assert result["max_frames"] == max_frames


@pytest.mark.parametrize("max_frames", [0, 25])
def test_make_report_arranges_unsupported_frame_limit_and_asserts_rejection(
    max_frames: int,
) -> None:
    # Arrange
    raw = {
        "patient_examination_id": 314,
        "knowledge_base_module": "clinical_reporting",
        "knowledge_base_version": "2.0.0",
        "patient": {
            "first_name": "Ada",
            "last_name": "Lovelace",
            "dob": "1815-12-10",
        },
        "max_frames": max_frames,
    }

    # Act
    def validate() -> PatientExaminationReportMakeReportPayload:
        return PatientExaminationReportMakeReportPayload.model_validate(raw)

    # Assert
    with pytest.raises(ValidationError):
        validate()


def test_persisted_artifacts_arrange_nullable_links_and_assert_canonical_response() -> (
    None
):
    # Arrange
    raw = {
        "full_report_id": 101,
        "pdf_id": None,
        "pdf_view_url": None,
        "pdf_download_url": None,
        "patient_timeline_url": "/api/media/patients/9/timeline/",
    }

    # Act
    payload = ReportPersistedArtifactsPayload.model_validate(raw)
    result = dump_persisted_artifacts_payload(payload)

    # Assert
    assert result == raw


@pytest.mark.parametrize(
    "invalid_artifacts",
    [
        {"full_report_id": 0},
        {"pdf_id": -1},
        {"pdf_id": 202, "unexpected": True},
    ],
)
def test_persisted_artifacts_arrange_invalid_shape_and_assert_rejection(
    invalid_artifacts: dict[str, object],
) -> None:
    # Arrange
    raw = invalid_artifacts

    # Act
    def validate() -> ReportPersistedArtifactsPayload:
        return ReportPersistedArtifactsPayload.model_validate(raw)

    # Assert
    with pytest.raises(ValidationError):
        validate()
