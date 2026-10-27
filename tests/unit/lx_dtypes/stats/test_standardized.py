import csv
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
import yaml

from lx_dtypes.models.contracts.aidataset_export import AIDataSetFrameAnnotationExport
from lx_dtypes.models.contracts.video_frame_annotations import (
    FrameBoxAnnotationBulkItemPayload,
)
from lx_dtypes.models.interface.DbInterface import DbInterface
from lx_dtypes.models.interface.KnowledgeBase import KnowledgeBase
from lx_dtypes.models.interface.Ledger import Ledger
from lx_dtypes.models.ledger.medical import (
    PatientMedicalLedger,
    PatientMedication,
    PatientMedicationSchedule,
)
from lx_dtypes.models.ledger.medical.Pydantic import (
    MedicationScheduleBlock,
    MedicationScheduleMedicationRow,
)
from lx_dtypes.stats.standardized import (
    CsvTable,
    interface_tables,
    ledger_tables,
    write_csv_tables,
)

NOW = datetime(2026, 1, 1, tzinfo=UTC)


def medication() -> PatientMedication:
    return PatientMedication.model_validate(
        {
            "uuid": "00000000-0000-4000-8000-000000000001",
            "patient": "patient-1",
            "medication": "mesalazine",
            "pzn": "04351736",
            "substances": [{"name": "mesalazine", "strength": "500 mg"}],
            "dosing": {"morning": "1"},
            "start_at": NOW,
            "end_at": NOW,
        }
    )


def test_complete_interface_and_empty_headers(
    star_ugi_knowledge_base: KnowledgeBase, tmp_path: Path
) -> None:
    tables = interface_tables(
        DbInterface(knowledge_base=star_ugi_knowledge_base, ledger=Ledger())
    )
    assert "knowledge_base/report_templates" in tables
    assert "ledger/p_indication_classifications" in tables
    assert "pzn" in tables["ledger/patient_medications"].columns
    assert "medication_blocks" in tables["ledger/patient_medication_schedules"].columns
    assert "external_annotation_id" in tables["ledger/image_annotations"].columns
    assert "image_width" in tables["ledger/image_box_annotations"].columns
    manifest = write_csv_tables(tables, tmp_path, source="test")
    assert len(yaml.safe_load(manifest.read_text())["tables"]) == len(tables)
    with (tmp_path / "ledger/patient_medications.csv").open() as stream:
        assert len(list(csv.reader(stream))) == 1


def test_medication_schedule_and_annotation_roundtrip(tmp_path: Path) -> None:
    med = medication()
    schedule = PatientMedicationSchedule(
        patient="patient-1",
        medications=[med],
        schedule_created_at=NOW,
        updated_at=NOW,
        medication_blocks=[
            MedicationScheduleBlock(
                rows=[MedicationScheduleMedicationRow(medication=med)]
            )
        ],
    )
    aggregate = PatientMedicalLedger(
        patient="patient-1", medications=[med], medication_schedules=[schedule]
    )
    image = AIDataSetFrameAnnotationExport.model_validate(
        {
            "annotation_id": 3,
            "frame_id": 4,
            "frame_number": 5,
            "relative_path": "frame.png",
            "patient_video_file_uuid": "video-record",
            "video_id": 6,
            "video_uuid": "video-uuid",
            "raw_video_hash": "synthetic-hash",
            "label": {"id": 1, "name": "polyp"},
            "value": False,
            "confidence": 0.0,
            "external_annotation_id": "external-3",
            "date_created": NOW,
            "date_modified": NOW,
        }
    )
    box = FrameBoxAnnotationBulkItemPayload(
        id=7,
        frame_id=4,
        label_id=1,
        information_source_name="manual_annotation",
        x=1.0,
        y=2.0,
        width=3.0,
        height=4.0,
        image_width=100,
        image_height=100,
    )
    tables = ledger_tables(
        Ledger(),
        medical_ledgers=[aggregate],
        image_annotations=[image],
        box_annotations=[box],
    )
    assert len(tables["patient_medications"].rows) == 1
    write_csv_tables(tables, tmp_path, source="test")

    def row(name: str) -> dict[str, str]:
        with (tmp_path / f"{name}.csv").open() as stream:
            return next(csv.DictReader(stream))

    exported = row("patient_medications")
    assert exported["pzn"] == med.pzn
    assert json.loads(exported["substances"]) == [
        {"name": "mesalazine", "strength": "500 mg"}
    ]
    assert json.loads(exported["dosing"])["morning"] == "1"
    assert exported["start_at"] == "2026-01-01T00:00:00Z"
    blocks = json.loads(row("patient_medication_schedules")["medication_blocks"])
    assert blocks[0]["rows"][0]["medication"] == str(med.uuid)
    assert row("image_annotations")["value"] == "false"
    assert row("image_annotations")["confidence"] == "0.0"
    assert json.loads(row("image_annotations")["label"])["name"] == "polyp"
    assert row("image_box_annotations")["frame_id"] == "4"
    assert row("image_box_annotations")["width"] == "3.0"


def test_conflicting_shared_medication_rejected() -> None:
    med = medication()
    changed = med.model_copy(update={"medication": "Different"})
    with pytest.raises(ValueError, match="Conflicting PatientMedication"):
        ledger_tables(
            Ledger(),
            medical_ledgers=[
                PatientMedicalLedger(patient="patient-1", medications=[med, changed]),
            ],
        )


def test_failed_export_preserves_existing_files(tmp_path: Path) -> None:
    original = CsvTable(columns=["text"], rows=[{"text": "=literal,\n日本語"}])
    write_csv_tables({"a": original}, tmp_path, source="test")
    before = {path.name: path.read_bytes() for path in tmp_path.iterdir()}
    invalid = CsvTable(columns=["value"], rows=[{"value": float("nan")}])
    with pytest.raises(ValueError):
        write_csv_tables(
            {"a": original, "z": invalid}, tmp_path, source="test", overwrite=True
        )
    assert {path.name: path.read_bytes() for path in tmp_path.iterdir()} == before
    with pytest.raises(FileExistsError):
        write_csv_tables({"a": original}, tmp_path, source="test")
    with pytest.raises(ValueError, match="Invalid table path"):
        write_csv_tables({"../escape": original}, tmp_path, source="test")


def test_case_only_examinations_are_exported_without_mutation() -> None:
    from lx_dtypes.models.ledger.case import Case
    from lx_dtypes.models.ledger.p_examination.Pydantic import PExamination

    exam = PExamination(patient="patient-1", examination="colonoscopy")
    case = Case(
        case_id="case-1",
        patient="patient-1",
        admission_date=NOW,
        patient_examinations=[exam],
    )
    ledger = Ledger(cases={str(case.uuid): case})
    tables = ledger_tables(ledger)
    assert len(tables["p_examinations"].rows) == 1
    assert tables["p_examinations"].rows[0]["uuid"] == str(exam.uuid)
    assert tables["cases"].rows[0]["patient_examinations"] == str(exam.uuid)
    assert ledger.patient_examinations == {}


def test_conflicting_examinations_rejected() -> None:
    from lx_dtypes.models.ledger.p_examination.Pydantic import PExamination

    exam = PExamination(patient="patient-1", examination="colonoscopy")
    changed = exam.model_copy(update={"examination": "gastroscopy"})
    with pytest.raises(ValueError, match="Conflicting examination"):
        ledger_tables(Ledger(patient_examinations={"first": exam, "second": changed}))


def frame_annotation(
    annotation_id: int, **overrides: object
) -> AIDataSetFrameAnnotationExport:
    data: dict[str, object] = {
        "annotation_id": annotation_id,
        "frame_id": 4,
        "frame_number": 5,
        "relative_path": "frame_000005.jpg",
        "patient_video_file_uuid": "video-record",
        "video_id": 6,
        "video_uuid": "video-uuid",
        "raw_video_hash": "synthetic-hash",
        "label": {"id": 1, "name": "polyp"},
        "value": True,
        "date_created": NOW,
        "date_modified": NOW,
    }
    data.update(overrides)
    return AIDataSetFrameAnnotationExport.model_validate(data)


def test_frames_table_deduplicates_frames_and_names_export_paths() -> None:
    tables = ledger_tables(
        Ledger(),
        image_annotations=[
            frame_annotation(1),
            frame_annotation(2, label={"id": 2, "name": "blood"}),
        ],
    )
    assert len(tables["image_annotations"].rows) == 2
    (frame,) = tables["frames"].rows
    assert frame["frame_id"] == 4
    assert frame["export_path"] == "frames/video-uuid/frame_000005.jpg"
    with pytest.raises(ValueError, match="Conflicting frame"):
        ledger_tables(
            Ledger(),
            image_annotations=[
                frame_annotation(1),
                frame_annotation(2, frame_number=99),
            ],
        )
    with pytest.raises(ValueError, match="Unsafe frame path"):
        ledger_tables(
            Ledger(), image_annotations=[frame_annotation(1, relative_path="../x.jpg")]
        )


def test_video_segments_and_states_are_exported(
    patient_video_file_fixture: object, p_video_segment_fixture: object
) -> None:
    from lx_dtypes.models.ledger.p_video import PatientVideoFile
    from lx_dtypes.models.ledger.p_video_segment import PVideoSegment

    assert isinstance(patient_video_file_fixture, PatientVideoFile)
    assert isinstance(p_video_segment_fixture, PVideoSegment)
    segment = PVideoSegment.model_validate(
        {
            **p_video_segment_fixture.model_dump(
                exclude={"patient_video_segment_state"}
            ),
            "uuid": "00000000-0000-4000-8000-0000000000aa",
        }
    )
    video = patient_video_file_fixture.model_copy(
        update={"patient_video_segments": {str(segment.uuid): segment}}
    )
    tables = ledger_tables(Ledger(patient_videos={str(video.uuid): video}))
    (video_row,) = tables["p_videos"].rows
    assert video_row["patient_video_segments"] == str(segment.uuid)
    assert video_row["anonymization_state"] == "anonymized"
    # Identifying metadata is referenced, never inlined.
    assert video_row["sensitive_meta"] == str(video.sensitive_meta.uuid)  # type: ignore[union-attr]
    (row,) = tables["p_video_segments"].rows
    assert row["uuid"] == str(segment.uuid)
    assert row["start_frame_number"] == 100
    assert row["label"] == "test_label"
    (state,) = tables["p_video_segment_states"].rows
    assert state["uuid"] == str(segment.state.uuid)
    assert state["patient_video_segment"] == str(segment.uuid)
    assert "is_validated" in tables["p_video_segment_states"].columns
    empty = ledger_tables(Ledger())
    assert empty["p_video_segments"].rows == []
    assert "timeline_coordinates" in empty["p_video_segments"].columns


def test_bundled_files_validated_and_failure_preserves_export(tmp_path: Path) -> None:
    table = CsvTable(columns=["frame_id"], rows=[{"frame_id": 4}])
    image = tmp_path / "frame.jpg"
    image.write_bytes(b"first")
    out = tmp_path / "export"
    path = "frames/video-uuid/frame_000005.jpg"
    manifest = write_csv_tables(
        {"frames": table}, out, source="test", files={path: image}
    )
    assert yaml.safe_load(manifest.read_text())["files"][path]["bytes"] == 5
    before = {
        item.relative_to(out): item.read_bytes()
        for item in out.rglob("*")
        if item.is_file()
    }
    image.write_bytes(b"second")
    with pytest.raises(FileNotFoundError):
        write_csv_tables(
            {"frames": table},
            out,
            source="test",
            overwrite=True,
            files={
                path: image,
                "frames/video-uuid/missing.jpg": tmp_path / "missing.jpg",
            },
        )
    after = {
        item.relative_to(out): item.read_bytes()
        for item in out.rglob("*")
        if item.is_file()
    }
    assert after == before
    for invalid in ("../escape.jpg", "frames/../x.jpg", "/abs.jpg", "frames.csv"):
        with pytest.raises(ValueError, match="Invalid bundled file path"):
            write_csv_tables(
                {"frames": table},
                out,
                source="test",
                overwrite=True,
                files={invalid: image},
            )
