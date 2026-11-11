"""Exact clock readings and signed offsets between explicitly recorded anchors."""

from datetime import UTC, datetime
from fractions import Fraction
from typing import Annotated, Literal

from pydantic import AwareDatetime, Field, field_validator

from lx_dtypes.models.model import FrozenContractModel


class _ClockTimestamp(FrozenContractModel):
    clock_id: str = Field(min_length=1, max_length=255, pattern=r"\S")


class _TickTimestamp(_ClockTimestamp):
    ticks: int
    time_base_num: int = Field(gt=0)
    time_base_den: int = Field(gt=0)

    @property
    def seconds(self) -> Fraction:
        return Fraction(self.ticks * self.time_base_num, self.time_base_den)


class PtsTimestamp(_TickTimestamp):
    """Native presentation ticks on an identified video generation's clock."""

    kind: Literal["pts"] = "pts"


class ElectrosurgeryTimestamp(_TickTimestamp):
    """Native generator ticks on one uninterrupted device clock epoch."""

    kind: Literal["electrosurgery"] = "electrosurgery"


class ExaminationTimestamp(_ClockTimestamp):
    """Timezone-aware examination time, normalized to UTC for storage."""

    kind: Literal["examination"] = "examination"
    timestamp: AwareDatetime

    @field_validator("timestamp")
    @classmethod
    def normalize_utc(cls, value: datetime) -> datetime:
        return value.astimezone(UTC)

    @property
    def seconds(self) -> Fraction:
        delta = self.timestamp - datetime(1970, 1, 1, tzinfo=UTC)
        return Fraction(
            (delta.days * 86400 + delta.seconds) * 1_000_000 + delta.microseconds,
            1_000_000,
        )


Timestamp = Annotated[
    PtsTimestamp | ElectrosurgeryTimestamp | ExaminationTimestamp,
    Field(discriminator="kind"),
]


class TimeOffset(FrozenContractModel):
    """Persist both clock anchors; offset seconds equal target minus reference.

    When anchors describe the same observed event on different clocks, adding
    this offset converts reference-clock seconds to target-clock seconds at
    that event. A single offset does not establish clock drift or frame ancestry.
    """

    schema_version: Literal["1"] = "1"
    reference: Timestamp
    target: Timestamp

    @property
    def offset_seconds(self) -> Fraction:
        return self.target.seconds - self.reference.seconds


__all__ = [
    "ElectrosurgeryTimestamp",
    "ExaminationTimestamp",
    "PtsTimestamp",
    "TimeOffset",
    "Timestamp",
]
