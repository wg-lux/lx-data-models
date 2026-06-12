from __future__ import annotations

from pydantic import BaseModel, ConfigDict, field_validator


class AssessmentRecord(BaseModel):
    model_config = ConfigDict(extra="ignore", strict=True)

    file: str = ""
    report_id: str = ""
    first_name: str = ""
    last_name: str = ""

    @field_validator("file", "report_id", "first_name", "last_name", mode="before")
    @classmethod
    def normalize_text_fields(cls, value: object) -> str:
        if value is None:
            return ""
        return str(value).strip()


__all__ = ["AssessmentRecord"]

