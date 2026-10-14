import pytest
from pydantic import ValidationError

from lx_dtypes.models.contracts.examination_revision import (
    CaseStudyExportSelection,
    ExaminationEvidence,
    ExaminationRevisionSnapshot,
)


@pytest.mark.parametrize(
    "evidence",
    [
        {},
        {"report_id": 1, "report_version": 2},
        {"video_id": 3},
        {
            "report_id": 1,
            "report_version": 2,
            "video_id": 3,
            "processed_sha256": "a" * 64,
        },
    ],
)
def test_optional_evidence_roundtrip(evidence: dict[str, object]) -> None:
    snapshot = ExaminationRevisionSnapshot.model_validate(
        {
            "content": {
                "examination": {
                    "patient": "1",
                    "examination": "example",
                    "uuid": "12345678-1234-1234-1234-123456789013",
                    "created_at": "2026-10-13T08:00:00Z",
                }
            },
            "evidence": evidence,
        }
    )
    assert ExaminationRevisionSnapshot.model_validate_json(
        snapshot.model_dump_json()
    ).model_dump(mode="json") == snapshot.model_dump(mode="json")


@pytest.mark.parametrize(
    "evidence",
    [
        {"report_id": 1},
        {"processed_sha256": "a" * 64},
        {"video_id": True},
        {"patient_name": "forbidden"},
    ],
)
def test_evidence_rejects_inconsistent_or_unknown_fields(
    evidence: dict[str, object],
) -> None:
    with pytest.raises(ValidationError):
        ExaminationEvidence.model_validate(evidence)


def test_study_export_rejects_duplicate_case_selections() -> None:
    with pytest.raises(ValidationError, match="unique"):
        CaseStudyExportSelection(case_ids=["12345678-1234-1234-1234-123456789012"] * 2)


def test_annotations_preserve_integer_timing_and_reject_mixed_generations() -> None:
    payload = {
        "video_id": 1,
        "processed_sha256": "a" * 64,
        "annotations": [
            {
                "annotation_id": 2,
                "frame_id": 3,
                "frame_number": 0,
                "presentation_timestamp": 9007199254740993,
                "stream_time_base_num": 1,
                "stream_time_base_den": 90000,
                "artifact_sha256": "a" * 64,
                "label_name": "synthetic",
                "value": False,
                "float_value": 0.0,
                "annotator": "example",
                "information_source_id": 4,
                "information_source_name": "manual",
            }
        ],
    }
    evidence = ExaminationEvidence.model_validate(payload)
    restored = ExaminationEvidence.model_validate_json(evidence.model_dump_json())
    assert restored == evidence
    assert restored.annotations[0].presentation_timestamp == 9007199254740993
    assert restored.annotations[0].value is False
    with pytest.raises(ValidationError, match="generation"):
        ExaminationEvidence.model_validate({**payload, "processed_sha256": "b" * 64})


def test_selected_export_validates_serialized_identity_and_finalization() -> None:
    import json

    from lx_dtypes.models.contracts.examination_revision import SelectedCaseExport

    record = {
        "patient_examination_id": 1,
        "revision_id": 2,
        "revision_version": 1,
        "finalized_at": "2026-10-13T09:00:00Z",
        "snapshot": {
            "content": {
                "examination": {
                    "patient": "1",
                    "examination": "example",
                    "uuid": "12345678-1234-1234-1234-123456789013",
                    "created_at": "2026-10-13T08:00:00Z",
                }
            },
            "evidence": {},
        },
    }
    payload = {
        "schema_version": "1.0",
        "generated_at": "2026-10-13T09:00:00Z",
        "case_id": "12345678-1234-1234-1234-123456789012",
        "patient_pseudonym": "synthetic",
        "center_key": None,
        "is_closed": False,
        "examinations": [record],
    }
    export = SelectedCaseExport.model_validate_json(json.dumps(payload))
    assert SelectedCaseExport.model_validate_json(export.model_dump_json()) == export
    for key, value in (
        ("revision_id", True),
        ("revision_id", "2"),
        ("finalized_at", None),
    ):
        with pytest.raises(ValidationError):
            SelectedCaseExport.model_validate_json(
                json.dumps({**payload, "examinations": [{**record, key: value}]})
            )
    with pytest.raises(ValidationError, match="only once"):
        SelectedCaseExport.model_validate_json(
            json.dumps({**payload, "examinations": [record, record]})
        )
