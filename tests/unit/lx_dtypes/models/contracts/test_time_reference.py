import json
from copy import deepcopy
from fractions import Fraction
from pathlib import Path

import pytest
from pydantic import ValidationError

from lx_dtypes.models.contracts import TimeOffsetEvidence, TimeOffsetExample
from lx_dtypes.models.contracts.package_snapshot import (
    PackageSnapshot,
    build_package_snapshot,
    restore_package_snapshot,
)
from lx_dtypes.models.interface.KnowledgeBase import KnowledgeBase
from lx_dtypes.models.interface.Ledger import Ledger
from lx_dtypes.models.interface.data_formats import read_record, write_record
from lx_dtypes.models.knowledge_base.time_reference import TimeReference
from lx_dtypes.models.ledger.p_time_offset import PTimeOffset
from lx_dtypes.packages import build_package, load_package

EXAMPLE = Path("docs/examples/dtypes_packages/time_references/config.yaml")


@pytest.fixture
def kb() -> KnowledgeBase:
    return load_package(EXAMPLE)


@pytest.fixture
def evidence(kb: KnowledgeBase) -> TimeOffsetEvidence:
    return kb.time_reference["video_generator_event"].examples[0].evidence


def test_yaml_package_loading_export_and_snapshot(kb: KnowledgeBase, tmp_path: Path):
    reference = kb.time_reference["video_generator_event"]
    assert reference.examples[0].role == "training"
    assert reference.examples[0].evidence.offset.offset_seconds == Fraction(1, 4)
    assert kb.export_record_lists()["time_references"][0]["name"] == reference.name
    snapshot = build_package_snapshot(kb)
    restored = restore_package_snapshot(
        PackageSnapshot.model_validate_json(snapshot.model_dump_json())
    )
    assert (
        restored.time_reference[reference.name].model_dump() == reference.model_dump()
    )
    path = tmp_path / "reference.yml"
    write_record(TimeReference, reference, path)
    assert read_record(TimeReference, path).model_dump() == reference.model_dump()


def test_ledger_serialization_and_versioned_validation(
    kb: KnowledgeBase, evidence: TimeOffsetEvidence, tmp_path: Path
):
    observation = PTimeOffset(
        patient_examination="exam-1",
        time_reference="video_generator_event",
        knowledge_base_module="time_references",
        knowledge_base_version="1.0.0",
        evidence=evidence,
    )
    kb.validate_time_offset(observation)
    assert PTimeOffset.model_validate(observation.ddict) == observation
    assert PTimeOffset.model_validate(observation.serialized_ddict) == observation
    ledger = Ledger(time_offsets={str(observation.uuid): observation})
    records = ledger.export_record_lists()
    assert "p_time_offsets" in records
    exported = records["p_time_offsets"][0]
    assert PTimeOffset.model_validate(exported) == observation
    path = tmp_path / "ledger.yml"
    write_record(Ledger, ledger, path)
    assert read_record(Ledger, path).time_offsets == ledger.time_offsets
    for field, value in [
        ("knowledge_base_version", "2.0.0"),
        ("knowledge_base_module", "other"),
        ("time_reference", "missing"),
    ]:
        invalid = observation.model_copy(update={field: value})
        with pytest.raises(ValueError):
            kb.validate_time_offset(invalid)


@pytest.mark.parametrize(
    "change",
    ["missing", "unused", "ticks", "time_base", "unverified_recording", "clock_kind"],
)
def test_rejects_mismatched_pts_references(evidence: TimeOffsetEvidence, change: str):
    data = evidence.model_dump(mode="json")
    # JSON validation exercises the same boundary as KB YAML and ledger files.
    if change == "missing":
        data["video_references"] = {}
    elif change == "unused":
        data["video_references"]["unused"] = deepcopy(
            data["video_references"]["video_generation_1"]
        )
    elif change == "ticks":
        data["offset"]["reference"]["ticks"] += 1
    elif change == "time_base":
        data["offset"]["reference"]["time_base_den"] = 1000
    elif change == "unverified_recording":
        data["video_references"]["video_generation_1"]["timeline"] = "recording"
    else:
        data["offset"]["target"]["clock_id"] = "video_generation_1"
    with pytest.raises(ValidationError):
        TimeOffsetEvidence.model_validate_json(json.dumps(data))


def test_verified_recording_reference(evidence: TimeOffsetEvidence):
    data = evidence.model_dump(mode="json")
    coordinates = data["video_references"]["video_generation_1"]["coordinates"]
    coordinates["recording_mapping_status"] = "verified"
    coordinates["recording"] = {
        "recording_content_hash": "b" * 64,
        "time_base_num": 1,
        "time_base_den": 90000,
        "first_frame_index": 90,
        "last_frame_index": 90,
        "first_presentation_timestamp": 180000,
        "last_presentation_timestamp": 180000,
    }
    data["video_references"]["video_generation_1"]["timeline"] = "recording"
    data["offset"]["reference"]["ticks"] = 180000
    restored = TimeOffsetEvidence.model_validate_json(json.dumps(data))
    assert restored.offset.offset_seconds == Fraction(-3, 4)


def test_example_roles_duplicates_and_kind_validation(evidence: TimeOffsetEvidence):
    for role in ("reference", "training", "validation", "test"):
        TimeOffsetExample.model_validate(
            {"example_id": role, "role": role, "evidence": evidence}
        )
    example = TimeOffsetExample(example_id="same", evidence=evidence)
    with pytest.raises(ValidationError, match="unique"):
        TimeReference(name="duplicates", examples=[example, example])
    with pytest.raises(ValidationError, match="clock kinds"):
        TimeReference(name="wrong", target_kind="examination", examples=[example])


def test_legacy_snapshot_without_time_family_preserves_digest():
    kb = KnowledgeBase.model_validate(
        {"config": {"name": "legacy", "version": "1.0.0"}}
    )
    snapshot = build_package_snapshot(kb)
    legacy = snapshot.model_dump(mode="json")
    del legacy["records"]["TimeReference"]
    restored = restore_package_snapshot(PackageSnapshot.model_validate(legacy))
    assert not restored.time_reference
    assert build_package_snapshot(restored).snapshot_id == snapshot.snapshot_id


def test_reference_from_dependency_resolves_owning_version(tmp_path: Path):
    manifest = build_package(
        tmp_path / "package",
        {
            "config.yaml": "name: combined\nversion: '2.0.0'\ndepends_on: [time_references]\n",
            "dependencies/time_references/config.yaml": EXAMPLE.read_text(),
            "dependencies/time_references/references.yml": EXAMPLE.with_name(
                "references.yml"
            ).read_text(),
        },
    )
    kb = load_package(manifest)
    reference = kb.time_reference["video_generator_event"]
    observation = PTimeOffset(
        patient_examination="exam-1",
        time_reference=reference.name,
        knowledge_base_module="time_references",
        knowledge_base_version="1.0.0",
        evidence=reference.examples[0].evidence,
    )
    kb.validate_time_offset(observation)
    with pytest.raises(ValueError, match="identity"):
        kb.validate_time_offset(
            observation.model_copy(update={"knowledge_base_version": "2.0.0"})
        )


def test_snapshot_detects_removed_training_data(kb: KnowledgeBase):
    payload = build_package_snapshot(kb).model_dump(mode="json")
    payload["records"]["TimeReference"] = []
    with pytest.raises(ValidationError, match="snapshot_id"):
        PackageSnapshot.model_validate(payload)
