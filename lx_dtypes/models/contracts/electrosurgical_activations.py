"""Per-activation HF generator summaries read from activation CSV exports.

One row is one HF activation as summarised by the generator: its start time,
manufacturer mode label and options, effect level, duration, average power,
delivered energy, socket slot and instrument. This is a different contract from
the sample-level ``ElectrosurgicalMeasurementSeries``; no curve can be derived
from it.

The export's timestamps carry no timezone. The caller must name the zone the
generator clock was set to; ambiguous or non-existent local times (daylight
saving transitions) are rejected rather than guessed. ``t`` is the activation
start: with that reading consecutive activations never overlap, which is
validated. Decimal columns are kept as ``Decimal`` without rounding.
"""

from __future__ import annotations

import csv
import hashlib
import io
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Final, Literal, Self
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import AwareDatetime, Field, ValidationError, model_validator

from lx_dtypes.models.model import FrozenContractModel

ACTIVATION_CSV_PARSER_ID: Final = "activation_summary_csv"
ACTIVATION_CSV_PARSER_VERSION: Final = "1"
ACTIVATION_CSV_COLUMNS: Final = (
    "",
    "t",
    "hfmode",
    "hfmode_options",
    "effect",
    "duration_s",
    "P_avg_W",
    "E_tot_J",
    "slot_number",
    "instrument",
)
MAX_ACTIVATION_CSV_BYTES: Final = 16 * 1024 * 1024
MAX_ACTIVATIONS: Final = 100_000
# Durations are exported with 0.1 s resolution; allow half of it before two
# consecutive activations count as overlapping.
_OVERLAP_TOLERANCE: Final = timedelta(milliseconds=50)


class ElectrosurgicalActivationCsvError(ValueError):
    """The file is not a valid activation CSV export; nothing is returned."""


class ElectrosurgicalActivation(FrozenContractModel):
    """One HF activation summary; values are exactly as exported."""

    source_row_index: int = Field(ge=0)
    started_at: AwareDatetime
    mode_label: str = Field(min_length=1, max_length=128)
    mode_options: str | None = Field(default=None, min_length=1, max_length=255)
    effect: Decimal = Field(ge=0, allow_inf_nan=False)
    duration_s: Decimal = Field(ge=0, allow_inf_nan=False)
    average_power_w: Decimal = Field(ge=0, allow_inf_nan=False)
    energy_j: Decimal = Field(ge=0, allow_inf_nan=False)
    slot_number: int = Field(ge=1)
    instrument: str = Field(min_length=1, max_length=128)

    @model_validator(mode="after")
    def validate_utc(self) -> Self:
        if self.started_at.utcoffset() != timedelta(0):
            raise ValueError("Activation start must be normalized to UTC")
        return self

    @property
    def ended_at(self) -> datetime:
        return self.started_at + timedelta(seconds=float(self.duration_s))


class ElectrosurgicalActivationLog(FrozenContractModel):
    """All activations of one export, bound to its bytes and parser version."""

    schema_version: Literal["1"] = "1"
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    parser_id: Literal["activation_summary_csv"] = ACTIVATION_CSV_PARSER_ID
    parser_version: Literal["1"] = ACTIVATION_CSV_PARSER_VERSION
    source_timezone: str = Field(min_length=1, max_length=64)
    activations: list[ElectrosurgicalActivation] = Field(
        min_length=1, max_length=MAX_ACTIVATIONS
    )

    @model_validator(mode="after")
    def validate_order(self) -> Self:
        for previous, current in zip(self.activations, self.activations[1:]):
            if current.source_row_index <= previous.source_row_index:
                raise ValueError("Source row indices must strictly increase")
            if current.started_at <= previous.started_at:
                raise ValueError("Activation starts must strictly increase")
            if previous.ended_at - _OVERLAP_TOLERANCE > current.started_at:
                raise ValueError(
                    f"Activation at row {previous.source_row_index} overlaps the next "
                    "one; 't' must be the activation start"
                )
        return self


def _decimal(value: str, column: str, row: int) -> Decimal:
    try:
        number = Decimal(value)
    except InvalidOperation as error:
        raise ElectrosurgicalActivationCsvError(
            f"Row {row}: column '{column}' is not a decimal number"
        ) from error
    if not number.is_finite():
        raise ElectrosurgicalActivationCsvError(
            f"Row {row}: column '{column}' must be finite"
        )
    return number


def _integer(value: str, column: str, row: int) -> int:
    if not value.isdigit():
        raise ElectrosurgicalActivationCsvError(
            f"Row {row}: column '{column}' is not a non-negative integer"
        )
    return int(value)


def _to_utc(value: str, zone: ZoneInfo, row: int) -> datetime:
    try:
        local = datetime.fromisoformat(value)
    except ValueError as error:
        raise ElectrosurgicalActivationCsvError(
            f"Row {row}: column 't' is not an ISO date-time"
        ) from error
    if local.tzinfo is not None:
        raise ElectrosurgicalActivationCsvError(
            f"Row {row}: column 't' unexpectedly carries a timezone"
        )
    early, late = local.replace(tzinfo=zone, fold=0), local.replace(tzinfo=zone, fold=1)
    converted = early.astimezone(UTC)
    # A skipped wall time (spring forward) does not round-trip.
    if converted.astimezone(zone).replace(tzinfo=None) != local:
        raise ElectrosurgicalActivationCsvError(
            f"Row {row}: local time {value} does not exist in {zone.key}"
        )
    # A repeated wall time (fall back) maps to two instants.
    if early.utcoffset() != late.utcoffset():
        raise ElectrosurgicalActivationCsvError(
            f"Row {row}: local time {value} is ambiguous in {zone.key}"
        )
    return converted


def parse_electrosurgical_activation_csv(
    content: bytes, *, source_timezone: str
) -> ElectrosurgicalActivationLog:
    """Validate an activation CSV export completely or raise; never partially.

    ``source_timezone`` is the IANA zone of the generator clock, for example
    ``Europe/Berlin``. It is required because the export omits offsets.
    """
    if len(content) > MAX_ACTIVATION_CSV_BYTES:
        raise ElectrosurgicalActivationCsvError("Activation CSV exceeds the size limit")
    try:
        zone = ZoneInfo(source_timezone)
    except (ZoneInfoNotFoundError, ValueError) as error:
        raise ElectrosurgicalActivationCsvError(
            f"Unknown timezone '{source_timezone}'"
        ) from error
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise ElectrosurgicalActivationCsvError(
            "Activation CSV must be UTF-8"
        ) from error

    reader = csv.reader(io.StringIO(text, newline=""), strict=True)
    try:
        header = next(reader)
    except StopIteration as error:
        raise ElectrosurgicalActivationCsvError("Activation CSV is empty") from error
    except csv.Error as error:
        raise ElectrosurgicalActivationCsvError(f"Malformed CSV: {error}") from error
    if tuple(header) != ACTIVATION_CSV_COLUMNS:
        raise ElectrosurgicalActivationCsvError(
            f"Unexpected columns {header}; expected {list(ACTIVATION_CSV_COLUMNS)}"
        )

    activations: list[ElectrosurgicalActivation] = []
    try:
        for row_number, row in enumerate(reader, start=2):
            if not row:
                continue
            if len(row) != len(ACTIVATION_CSV_COLUMNS):
                raise ElectrosurgicalActivationCsvError(
                    f"Line {row_number}: expected {len(ACTIVATION_CSV_COLUMNS)} "
                    f"fields, found {len(row)}"
                )
            if len(activations) >= MAX_ACTIVATIONS:
                raise ElectrosurgicalActivationCsvError(
                    "Activation CSV exceeds the row limit"
                )
            values = dict(zip(ACTIVATION_CSV_COLUMNS, row, strict=True))
            options = values["hfmode_options"].strip()
            try:
                activations.append(
                    ElectrosurgicalActivation(
                        source_row_index=_integer(values[""], "index", row_number),
                        started_at=_to_utc(values["t"], zone, row_number),
                        mode_label=values["hfmode"].strip(),
                        mode_options=options or None,
                        effect=_decimal(values["effect"], "effect", row_number),
                        duration_s=_decimal(
                            values["duration_s"], "duration_s", row_number
                        ),
                        average_power_w=_decimal(
                            values["P_avg_W"], "P_avg_W", row_number
                        ),
                        energy_j=_decimal(values["E_tot_J"], "E_tot_J", row_number),
                        slot_number=_integer(
                            values["slot_number"], "slot_number", row_number
                        ),
                        instrument=values["instrument"].strip(),
                    )
                )
            except ValidationError as error:
                raise ElectrosurgicalActivationCsvError(
                    f"Line {row_number}: {error.errors()[0]['msg']}"
                ) from error
    except csv.Error as error:
        raise ElectrosurgicalActivationCsvError(f"Malformed CSV: {error}") from error

    try:
        return ElectrosurgicalActivationLog(
            source_sha256=hashlib.sha256(content).hexdigest(),
            source_timezone=zone.key,
            activations=activations,
        )
    except ValidationError as error:
        raise ElectrosurgicalActivationCsvError(error.errors()[0]["msg"]) from error


def read_electrosurgical_activation_csv(
    path: Path, *, source_timezone: str
) -> ElectrosurgicalActivationLog:
    """Read a file within the size limit and parse it."""
    with path.open("rb") as handle:
        content = handle.read(MAX_ACTIVATION_CSV_BYTES + 1)
    return parse_electrosurgical_activation_csv(
        content, source_timezone=source_timezone
    )


def activations_by_mode(
    log: ElectrosurgicalActivationLog,
) -> dict[str, Sequence[ElectrosurgicalActivation]]:
    """Group activations by their exact manufacturer mode label, in log order."""
    grouped: dict[str, list[ElectrosurgicalActivation]] = {}
    for activation in log.activations:
        grouped.setdefault(activation.mode_label, []).append(activation)
    return dict(grouped)


__all__ = [
    "ACTIVATION_CSV_COLUMNS",
    "ACTIVATION_CSV_PARSER_ID",
    "ACTIVATION_CSV_PARSER_VERSION",
    "MAX_ACTIVATIONS",
    "MAX_ACTIVATION_CSV_BYTES",
    "ElectrosurgicalActivation",
    "ElectrosurgicalActivationCsvError",
    "ElectrosurgicalActivationLog",
    "activations_by_mode",
    "parse_electrosurgical_activation_csv",
    "read_electrosurgical_activation_csv",
]
