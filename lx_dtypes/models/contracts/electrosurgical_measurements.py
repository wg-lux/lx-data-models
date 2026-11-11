"""Typed high-frequency (HF) electrosurgical generator measurements.

An HF electrosurgical generator delivers radio-frequency current for cutting and
coagulation during endoscopy. Its measurements are recorded on the generator's
own clock, which is independent of the video recorder. A measurement series
therefore keeps the generator's native integer ticks and rational time base
(``ElectricalTimestampSeries``) and attaches one or more value channels that are
sampled at exactly those ticks. Channels with a different sample rate belong to
a separate series on the same clock.

Each quantity has exactly one canonical UCUM unit. Producers convert at their
parser boundary; this contract never converts units or fills missing values.
"""

from __future__ import annotations

import math
from typing import Final, Literal, Self

from pydantic import Field, model_validator

from lx_dtypes.models.model import FrozenContractModel

from .video_provenance import ElectricalTimestampSeries

MAX_ELECTRICAL_SAMPLES: Final = 2_000_000
MAX_ELECTRICAL_CHANNELS: Final = 32

ElectrosurgicalQuantity = Literal[
    "voltage_peak",
    "voltage_rms",
    "current_rms",
    "power",
    "impedance",
    "energy",
    "activation",
]
ElectrosurgicalUnit = Literal["V", "A", "W", "Ohm", "J", "1"]

CANONICAL_ELECTROSURGICAL_UNITS: Final[
    dict[ElectrosurgicalQuantity, ElectrosurgicalUnit]
] = {
    "voltage_peak": "V",
    "voltage_rms": "V",
    "current_rms": "A",
    "power": "W",
    "impedance": "Ohm",
    "energy": "J",
    "activation": "1",
}


class ElectrosurgicalChannel(FrozenContractModel):
    """One measured quantity, one value per timestamp of the owning series.

    ``activation`` is 1 while the generator delivers HF energy and 0 otherwise.
    ``energy`` is the cumulative delivered energy reported by the generator.
    """

    channel_id: str = Field(pattern=r"^[a-z][a-z0-9_]{0,63}$")
    quantity: ElectrosurgicalQuantity
    unit: ElectrosurgicalUnit
    values: list[float] = Field(min_length=1, max_length=MAX_ELECTRICAL_SAMPLES)

    @model_validator(mode="after")
    def validate_values(self) -> Self:
        expected = CANONICAL_ELECTROSURGICAL_UNITS[self.quantity]
        if self.unit != expected:
            raise ValueError(
                f"Quantity {self.quantity} requires unit {expected}, got {self.unit}"
            )
        if not all(math.isfinite(value) for value in self.values):
            raise ValueError("Electrical channel values must be finite")
        if self.quantity == "activation":
            if any(value not in (0.0, 1.0) for value in self.values):
                raise ValueError("Activation values must be 0 or 1")
        elif any(value < 0 for value in self.values):
            raise ValueError(f"{self.quantity} values must be nonnegative")
        return self


class ElectrosurgicalMeasurementSeries(FrozenContractModel):
    """Lossless HF generator samples bound to their source file and clock epoch."""

    schema_version: Literal["1"] = "1"
    source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    parser_id: str = Field(pattern=r"^[a-z][a-z0-9_.-]{0,63}$")
    parser_version: str = Field(min_length=1, max_length=64)
    timestamps: ElectricalTimestampSeries
    channels: list[ElectrosurgicalChannel] = Field(
        min_length=1, max_length=MAX_ELECTRICAL_CHANNELS
    )

    @model_validator(mode="after")
    def validate_channels(self) -> Self:
        sample_count = len(self.timestamps.presentation_timestamps)
        if sample_count > MAX_ELECTRICAL_SAMPLES:
            raise ValueError("Electrical series exceeds the sample limit")
        channel_ids = [channel.channel_id for channel in self.channels]
        if len(set(channel_ids)) != len(channel_ids):
            raise ValueError("Electrical channel identifiers must be unique")
        if any(len(channel.values) != sample_count for channel in self.channels):
            raise ValueError("Every channel requires exactly one value per timestamp")
        return self


__all__ = [
    "CANONICAL_ELECTROSURGICAL_UNITS",
    "MAX_ELECTRICAL_CHANNELS",
    "MAX_ELECTRICAL_SAMPLES",
    "ElectrosurgicalChannel",
    "ElectrosurgicalMeasurementSeries",
    "ElectrosurgicalQuantity",
    "ElectrosurgicalUnit",
]
