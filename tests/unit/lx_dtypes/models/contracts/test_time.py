from datetime import UTC, datetime, timedelta, timezone
from fractions import Fraction
from pathlib import Path

import pytest
from pydantic import ValidationError

from lx_dtypes.models.contracts import (
    ElectrosurgeryTimestamp,
    ExaminationTimestamp,
    PtsTimestamp,
    TimeOffset,
)
from lx_dtypes.models.interface.data_formats import read_record, write_record


@pytest.mark.parametrize("ticks", [-3001, 0, 3001, 2**60 + 1])
def test_tick_offsets_are_exact_and_survive_yaml(tmp_path: Path, ticks: int):
    reference = PtsTimestamp(
        clock_id="video-generation-1", ticks=1, time_base_num=1001, time_base_den=30000
    )
    target = ElectrosurgeryTimestamp(
        clock_id="generator-epoch-1", ticks=ticks, time_base_num=1, time_base_den=1000
    )
    offset = TimeOffset(reference=reference, target=target)
    assert offset.offset_seconds == Fraction(ticks, 1000) - Fraction(1001, 30000)
    path = tmp_path / "offset.yml"
    write_record(TimeOffset, offset, path)
    restored = read_record(TimeOffset, path)
    assert restored == offset
    assert restored.offset_seconds == offset.offset_seconds
    assert (
        TimeOffset(reference=target, target=reference).offset_seconds
        == -offset.offset_seconds
    )


@pytest.mark.parametrize("year", [1960, 2026])
def test_examination_offset_and_utc_round_trip(tmp_path: Path, year: int):
    examination = ExaminationTimestamp(
        clock_id="examination-1",
        timestamp=datetime(
            year, 1, 1, 12, 0, 0, 123456, tzinfo=timezone(timedelta(hours=2))
        ),
    )
    assert examination.timestamp == datetime(year, 1, 1, 10, 0, 0, 123456, tzinfo=UTC)
    assert examination.timestamp.utcoffset() == timedelta(0)
    pts = PtsTimestamp(clock_id="video-1", ticks=1, time_base_num=1, time_base_den=3)
    offset = TimeOffset(reference=pts, target=examination)
    whole_seconds = (
        datetime(year, 1, 1, 10, tzinfo=UTC) - datetime(1970, 1, 1, tzinfo=UTC)
    ).days * 86400 + 36000
    assert offset.offset_seconds == whole_seconds + Fraction(
        123456, 1_000_000
    ) - Fraction(1, 3)
    path = tmp_path / "examination-offset.yml"
    write_record(TimeOffset, offset, path)
    assert read_record(TimeOffset, path) == offset
    assert TimeOffset.model_validate_json(offset.model_dump_json()) == offset


@pytest.mark.parametrize(
    "invalid",
    [
        {"ticks": True},
        {"ticks": 1.5},
        {"ticks": "1"},
        {"time_base_num": 0},
        {"time_base_den": 0},
        {"time_base_den": -1},
        {"clock_id": " "},
        {"unexpected": 1},
    ],
)
def test_invalid_tick_readings_are_rejected(invalid: dict[str, object]):
    payload = {
        "clock_id": "video-1",
        "ticks": 1,
        "time_base_num": 1,
        "time_base_den": 1000,
    }
    with pytest.raises(ValidationError):
        PtsTimestamp.model_validate(payload | invalid)


def test_naive_examination_and_unknown_timestamp_kind_are_rejected():
    with pytest.raises(ValidationError):
        ExaminationTimestamp(clock_id="exam-1", timestamp=datetime(2026, 1, 1))
    with pytest.raises(ValidationError):
        TimeOffset.model_validate_json(
            '{"reference":{"kind":"unknown"},"target":{"kind":"unknown"}}'
        )


def test_electrosurgery_to_examination_and_zero_offsets(tmp_path: Path):
    electrical = ElectrosurgeryTimestamp(
        clock_id="generator-1", ticks=250, time_base_num=1, time_base_den=1000
    )
    examination = ExaminationTimestamp(
        clock_id="exam-1", timestamp=datetime(1970, 1, 1, 0, 0, 0, 250000, tzinfo=UTC)
    )
    zero = TimeOffset(reference=electrical, target=examination)
    assert zero.offset_seconds == 0
    path = tmp_path / "zero-offset.yml"
    write_record(TimeOffset, zero, path)
    assert read_record(TimeOffset, path).offset_seconds == 0


def test_naive_examination_in_json_is_rejected():
    with pytest.raises(ValidationError):
        ExaminationTimestamp.model_validate_json(
            '{"clock_id":"exam-1","timestamp":"2026-01-01T12:00:00"}'
        )
