"""Shared clinical period fields; host persistence remains outside lx-dtypes."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Literal, Self

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from lx_dtypes.models.contracts.german_fhir import Pzn
from lx_dtypes.models.contracts.json_types import JsonValue


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


_MAX_ONE_LINE_BREAK = 1

# BMP (bundeseinheitlicher Medikationsplan) dosing-slot grammar, confirmed against the
# real `dosierungTyp` simple type in bmp_V2.8.xsd.
_DOSING_SLOT_PATTERN = re.compile(
    r"([1-9]\d{0,3})|([1-9]\d,\d)|(\d,\d{1,2})|1/8|1/2|2/3|1/3|1/4|3/4"
)

# BMP's confirmed sub-heading (Zwischenüberschrift) codes from the XSD enum. 420 is
# intentionally absent.
_HEADING_CODE = Literal[
    411, 412, 413, 414, 415, 416, 417, 418, 419, 421, 422, 423, 424, 425
]


def validate_line_breaks(value: str | None, max_breaks: int) -> None:
    if value is not None and value.count("\n") > max_breaks:
        raise ValueError(f"must not contain more than {max_breaks} line break(s)")


class MedicationSubstance(BaseModel):
    """One active substance of a medication entry.

    BMP allows up to 3 of these per medication entry (``<W>``); order is
    significant and must match the order of strengths on the printed plan.
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    name: str = Field(min_length=1, max_length=80)
    strength: str | None = Field(default=None, min_length=1, max_length=15)


class MedicationDosingSchedule(BaseModel):
    """BMP-compatible dosing scheme.

    Either the 4 day-segment quantities (``morning``/``noon``/``evening``/``night``,
    optionally with a ``weekday`` for once-weekly dosing), or ``free_text`` — never
    both. An entirely empty instance ("no dosing info recorded") is also legal, since
    BMP does not require a dosing scheme on every medication entry.
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    morning: str | None = None
    noon: str | None = None
    evening: str | None = None
    night: str | None = None
    weekday: int | None = Field(default=None, ge=1, le=7)
    free_text: str | None = Field(default=None, min_length=1, max_length=20)

    @field_validator("morning", "noon", "evening", "night")
    @classmethod
    def validate_slot_grammar(cls, value: str | None) -> str | None:
        if value is not None and not _DOSING_SLOT_PATTERN.fullmatch(value):
            raise ValueError(
                "dosing slot must be an integer with no leading zero, a comma "
                "decimal, or one of 1/8, 1/2, 2/3, 1/3, 1/4, 3/4"
            )
        return value

    @model_validator(mode="after")
    def validate_shape(self) -> Self:
        has_slot = any(
            value is not None
            for value in (self.morning, self.noon, self.evening, self.night)
        )
        if self.free_text is not None and has_slot:
            raise ValueError(
                "free_text must not be combined with the structured dosing slots"
            )
        if self.weekday is not None and not has_slot:
            raise ValueError("weekday requires at least one dosing slot to be set")
        return self

    def is_empty(self) -> bool:
        return (
            self.morning is None
            and self.noon is None
            and self.evening is None
            and self.night is None
            and self.weekday is None
            and self.free_text is None
        )


class MedicationScheduleHeading(BaseModel):
    """Zwischenüberschrift: a controlled code or free text, never both."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    code: _HEADING_CODE | None = None
    text: str | None = Field(default=None, min_length=1, max_length=50)

    @model_validator(mode="after")
    def validate_exclusive(self) -> Self:
        if (self.code is None) == (self.text is None):
            raise ValueError("exactly one of code and text must be provided")
        return self


class MedicationScheduleFreeTextLine(BaseModel):
    """Freitextzeile: a free-text line not tied to any medication entry."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    text: str = Field(min_length=1, max_length=200)

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        validate_line_breaks(value, _MAX_ONE_LINE_BREAK)
        return value


class MedicationScheduleCompoundEntry(BaseModel):
    """Rezeptureintrag: a compounded-preparation entry with an optional bound note."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    text: str = Field(min_length=1, max_length=200)
    bound_note: str | None = Field(default=None, min_length=1, max_length=200)

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        validate_line_breaks(value, _MAX_ONE_LINE_BREAK)
        return value

    @field_validator("bound_note")
    @classmethod
    def validate_bound_note(cls, value: str | None) -> str | None:
        validate_line_breaks(value, _MAX_ONE_LINE_BREAK)
        return value


class MedicationEntryFields(BaseModel):
    """Shared BMP-aligned fields of a medication entry (BMP ``<M>``).

    Reused as-is by both the ledger read model (`PatientMedication`) and the write
    contracts (`PatientMedicationCreate`/`PatientMedicationUpdate`) -- this field mixin
    deliberately inherits configuration from its concrete model, matching
    `MedicationPeriodFields`.

    Note: the "at least one field must be set" completeness rule is intentionally
    NOT enforced here, since `PatientMedicationUpdate` is a partial patch where an
    all-empty mixin state does not mean an all-empty persisted record. Concrete
    models that represent a complete entry (`PatientMedication`,
    `PatientMedicationCreate`) must add their own `is_entirely_blank()`-based check.
    """

    # Legacy host dosage is preserved verbatim; it is never inferred as BMP dosing.
    dosage: JsonValue = None
    intake_times: list[str] = Field(default_factory=list)

    @field_validator("intake_times")
    @classmethod
    def validate_intake_times(cls, values: list[str]) -> list[str]:
        if any(not value.strip() for value in values) or len(values) != len(
            set(values)
        ):
            raise ValueError("intake_times must contain unique nonempty references")
        return values

    medication: str | None = Field(default=None, min_length=1)
    medication_indication: str | None = Field(default=None, min_length=1, max_length=50)
    pzn: Pzn | None = None
    substances: list[MedicationSubstance] = Field(default_factory=list, max_length=3)
    dosing: MedicationDosingSchedule = Field(default_factory=MedicationDosingSchedule)
    dosage_form: str | None = Field(default=None, min_length=1)
    dosage_form_code: str | None = Field(default=None, min_length=1, max_length=10)
    unit: str | None = Field(default=None, min_length=1)
    unit_code: str | None = Field(default=None, pattern=r"^[#0-9a-v]$")
    notes: str | None = Field(default=None, min_length=1, max_length=80)
    bound_note: str | None = Field(default=None, min_length=1, max_length=200)

    @field_validator("medication_indication", "notes", "bound_note")
    @classmethod
    def validate_free_text_line_breaks(cls, value: str | None) -> str | None:
        validate_line_breaks(value, _MAX_ONE_LINE_BREAK)
        return value

    @model_validator(mode="after")
    def validate_exclusive_fields(self) -> Self:
        if self.dosing.weekday is not None and self.bound_note is not None:
            raise ValueError("weekly dosing must not have a bound_note")
        if (
            self.dosage is not None or self.intake_times
        ) and not self.dosing.is_empty():
            raise ValueError(
                "legacy dosage/intake_times and BMP dosing are mutually exclusive"
            )
        if self.dosage_form is not None and self.dosage_form_code is not None:
            raise ValueError(
                "at most one of dosage_form and dosage_form_code may be set"
            )
        if self.unit is not None and self.unit_code is not None:
            raise ValueError("at most one of unit and unit_code may be set")
        return self

    def is_entirely_blank(self) -> bool:
        """Return True if none of the identifying/descriptive fields are set.

        Mirrors the BMP XSD rule on ``<M>``: "at least one attribute or one ``<W>``
        must be given". Callers that represent a complete entry should reject this
        state; `PatientMedicationUpdate` must not call this (see class docstring).
        """

        return (
            self.medication is None
            and self.pzn is None
            and not self.substances
            and self.dosing.is_empty()
            and self.dosage_form is None
            and self.dosage_form_code is None
            and self.unit is None
            and self.unit_code is None
            and self.notes is None
            and self.medication_indication is None
            and self.bound_note is None
        )


__all__ = [
    "MedicationDosingSchedule",
    "MedicationEntryFields",
    "MedicationPeriodFields",
    "MedicationScheduleCompoundEntry",
    "MedicationScheduleFreeTextLine",
    "MedicationScheduleHeading",
    "MedicationSubstance",
    "validate_line_breaks",
]
