from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TextAnonymizationMeta(BaseModel):
    model_config = ConfigDict(extra="ignore", strict=True)

    pdf_hash: str = ""
    file_path: str = ""
    first_name: str = ""
    last_name: str = ""
    examiner_first_name: str = ""
    examiner_last_name: str = ""
    casenumber: str = ""
    examination_date: str = ""
    dob: str = ""

    @field_validator(
        "pdf_hash",
        "file_path",
        "first_name",
        "last_name",
        "examiner_first_name",
        "examiner_last_name",
        "casenumber",
        "examination_date",
        "dob",
        mode="before",
    )
    @classmethod
    def normalize_text(cls, value: str | int | None) -> str:
        if value is None:
            return ""
        return str(value).strip()


class GenderGuess(str, Enum):
    MALE = "male"
    MOSTLY_MALE = "mostly_male"
    FEMALE = "female"
    MOSTLY_FEMALE = "mostly_female"
    UNKNOWN = "unknown"
    ANDY = "andy"


class GenderDisplayLabel(str, Enum):
    MALE = "Male"
    FEMALE = "Female"
    NEUTRAL = "Neutral"


class DateOfBirthCore(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    day: int = Field(ge=1, le=31)
    month: int = Field(ge=1, le=12)
    year: int = Field(ge=1900, le=2100)


class PersonNameMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    first_name: str
    last_name: str
    dob: DateOfBirthCore
    gender_label: GenderDisplayLabel

    @field_validator("first_name", "last_name", mode="before")
    @classmethod
    def normalize_name(cls, value: str | float | bool | None) -> str:
        text = str(value).strip()
        if not text:
            raise ValueError("name components must not be empty")
        return text


class LLMMetadataPayload(BaseModel):
    model_config = ConfigDict(extra="ignore", strict=True)

    first_name: str = ""
    last_name: str = ""
    gender: str = ""
    dob: str = ""
    casenumber: str = ""
    examination_date: str = ""
    examination_time: str = ""
    examiner_first_name: str = ""
    examiner_last_name: str = ""

    @field_validator(
        "first_name",
        "last_name",
        "gender",
        "dob",
        "casenumber",
        "examination_date",
        "examination_time",
        "examiner_first_name",
        "examiner_last_name",
        mode="before",
    )
    @classmethod
    def normalize_text_fields(cls, value: str | int | None) -> str:
        if value is None:
            return ""
        return str(value).strip()


__all__ = [
    "DateOfBirthCore",
    "GenderDisplayLabel",
    "GenderGuess",
    "LLMMetadataPayload",
    "PersonNameMetadata",
    "TextAnonymizationMeta",
]
