from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from lx_dtypes.models.contracts.electrosurgical_activations import (
    ElectrosurgicalActivationCsvError,
    ElectrosurgicalActivationLog,
    activations_by_mode,
    parse_electrosurgical_activation_csv,
    read_electrosurgical_activation_csv,
)
from tests.paths import REPOSITORY_ROOT

FIXTURE = (
    REPOSITORY_ROOT
    / "tests/fixtures/lx_dtypes/electrosurgery/synthetic_activations.csv"
)
HEADER = (
    ",t,hfmode,hfmode_options,effect,duration_s,P_avg_W,E_tot_J,slot_number,instrument"
)


def _csv(*rows: str, header: str = HEADER) -> bytes:
    return ("\r\n".join([header, *rows]) + "\r\n").encode()


def _row(index: int, t: str, duration: str = "0.4", **overrides: str) -> str:
    values = {
        "hfmode": "softCOAG",
        "hfmode_options": "",
        "effect": "4.5",
        "P_avg_W": "12.9",
        "E_tot_J": "6.0",
        "slot_number": "3",
        "instrument": "Monopolar",
        **overrides,
    }
    return (
        f"{index},{t},{values['hfmode']},{values['hfmode_options']},{values['effect']},"
        f"{duration},{values['P_avg_W']},{values['E_tot_J']},"
        f"{values['slot_number']},{values['instrument']}"
    )


def test_reads_export_format_losslessly() -> None:
    log = read_electrosurgical_activation_csv(FIXTURE, source_timezone="Europe/Berlin")

    assert log.source_sha256 == hashlib.sha256(FIXTURE.read_bytes()).hexdigest()
    assert len(log.activations) == 7
    first, _, bipolar, cut, apc, apc_without_mode, _ = log.activations
    # Winter time in Berlin is UTC+1.
    assert first.started_at == datetime(2000, 1, 3, 8, 0, tzinfo=UTC)
    assert first.duration_s == Decimal("0.0") and first.mode_options is None
    assert (bipolar.instrument, bipolar.slot_number) == ("Bipolar", 1)
    assert cut.mode_label == "endoCUT Q"
    assert cut.mode_options == "interval: 6, duration: 1"
    assert apc.mode_options == "flow 0.8l/min, fast"
    assert apc_without_mode.average_power_w == Decimal("141.9")
    assert str(cut.energy_j) == "11.0"
    assert {mode: len(rows) for mode, rows in activations_by_mode(log).items()} == {
        "sprayCOAG": 2,
        "softCOAG bipolar": 1,
        "endoCUT Q": 1,
        "pulsedAPC": 2,
        "highCUT": 1,
    }
    assert (
        ElectrosurgicalActivationLog.model_validate_json(log.model_dump_json()) == log
    )


def test_summer_time_and_utf8_bom() -> None:
    content = b"\xef\xbb\xbf" + _csv(_row(0, "2000-07-03 09:00:00"))
    log = parse_electrosurgical_activation_csv(content, source_timezone="Europe/Berlin")
    assert log.activations[0].started_at == datetime(2000, 7, 3, 7, 0, tzinfo=UTC)


@pytest.mark.parametrize(
    ("content", "timezone", "message"),
    [
        (_csv(_row(0, "2000-01-03 09:00:00")), "Mars/Base", "Unknown timezone"),
        (
            _csv(_row(0, "2000-01-03 09:00:00"), header=HEADER + ",extra"),
            "UTC",
            "Unexpected columns",
        ),
        (_csv(_row(0, "2000-01-03 09:00:00") + ",x"), "UTC", "expected 10 fields"),
        (_csv(_row(0, "2000-01-03T09:00:00+01:00")), "UTC", "carries a timezone"),
        (_csv(_row(0, "yesterday")), "UTC", "not an ISO date-time"),
        (_csv(_row(0, "2000-01-03 09:00:00", duration="NaN")), "UTC", "must be finite"),
        (
            _csv(_row(0, "2000-01-03 09:00:00", duration="1,5")),
            "UTC",
            "expected 10 fields",
        ),
        (
            _csv(_row(0, "2000-01-03 09:00:00", duration="-0.1")),
            "UTC",
            "greater than or equal",
        ),
        (
            _csv(_row(0, "2000-01-03 09:00:00", slot_number="0")),
            "UTC",
            "greater than or equal",
        ),
        (
            _csv(_row(0, "2000-01-03 09:00:00", hfmode=" ")),
            "UTC",
            "at least 1 character",
        ),
        (_csv(_row(0, "2000-03-26 02:30:00")), "Europe/Berlin", "does not exist"),
        (_csv(_row(0, "2000-10-29 02:30:00")), "Europe/Berlin", "ambiguous"),
        (
            _csv(_row(0, "2000-01-03 09:00:00"), _row(1, "2000-01-03 09:00:00")),
            "UTC",
            "starts must strictly increase",
        ),
        (
            _csv(_row(1, "2000-01-03 09:00:00"), _row(1, "2000-01-03 09:00:05")),
            "UTC",
            "row indices must strictly increase",
        ),
        (
            # A 2 s activation cannot be followed by another start 1 s later.
            _csv(_row(0, "2000-01-03 09:00:00", "2.0"), _row(1, "2000-01-03 09:00:01")),
            "UTC",
            "overlaps",
        ),
        (_csv(), "UTC", "at least 1 item"),
        (b"\xff\xfe", "UTC", "must be UTF-8"),
    ],
)
def test_invalid_exports_fail_without_partial_result(
    content: bytes, timezone: str, message: str
) -> None:
    with pytest.raises(ElectrosurgicalActivationCsvError, match=message):
        parse_electrosurgical_activation_csv(content, source_timezone=timezone)


def test_overlap_tolerance_matches_export_resolution() -> None:
    # Durations are rounded to 0.1 s: 1.05 s shown as 1.0 or 1.1 is not an overlap.
    content = _csv(
        _row(0, "2000-01-03 09:00:00.000000", "1.1"),
        _row(1, "2000-01-03 09:00:01.060000"),
    )
    log = parse_electrosurgical_activation_csv(content, source_timezone="UTC")
    assert len(log.activations) == 2


def test_oversized_file_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "large.csv"
    path.write_bytes(_csv(_row(0, "2000-01-03 09:00:00")) + b" " * (16 * 1024 * 1024))
    with pytest.raises(ElectrosurgicalActivationCsvError, match="size limit"):
        read_electrosurgical_activation_csv(path, source_timezone="UTC")
