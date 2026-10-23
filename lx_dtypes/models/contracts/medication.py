"""Shared clinical period fields; host persistence remains outside lx-dtypes."""

from datetime import datetime
from typing import Self

from pydantic import AwareDatetime, BaseModel, field_validator, model_validator


class MedicationPeriodFields(BaseModel):
    """Optional known treatment interval, independent of the active flag.

    This field mixin deliberately inherits configuration from its concrete model.
    """

    start_at: AwareDatetime | None = None
    end_at: AwareDatetime | None = None

    @field_validator("start_at", "end_at", mode="before")
    @classmethod
    def parse_period_datetime(cls, value: object) -> object:
        return datetime.fromisoformat(value) if isinstance(value, str) else value

    @model_validator(mode="after")
    def validate_period(self) -> Self:
        if self.end_at is not None:
            if self.start_at is None:
                raise ValueError("end_at requires start_at")
            if self.end_at < self.start_at:
                raise ValueError("end_at must not be earlier than start_at")
        return self
