from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StudyCohortMediaRow(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    id: int = Field(ge=1)
    stream_url: str = Field(min_length=1)
    availability: str = Field(min_length=1)


class StudyCohortReportRow(StudyCohortMediaRow):
    document_type: str


class StudyCohortExaminationRow(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    patient_examination_id: int = Field(ge=1)
    case_hash: str = Field(min_length=1)
    examination_name: str
    examination_date: date | None = None


class StudyCohortCaseRow(BaseModel):
    """One pseudonymous patient row with all matching examination occurrences."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    # Retained as the latest examination for additive consumer compatibility.
    patient_examination_id: int = Field(ge=1)
    case_hash: str = Field(min_length=1)
    examination_name: str
    examination_date: date | None = None

    patient_hash: str = Field(min_length=1)
    patient_examination_ids: list[int] = Field(min_length=1)
    case_hashes: list[str] = Field(min_length=1)
    examinations: list[StudyCohortExaminationRow] = Field(min_length=1)
    center_keys: list[str] = Field(default_factory=list)
    findings: list[str] = Field(default_factory=list)
    annotation_labels: list[str] = Field(default_factory=list)
    reports: list[StudyCohortReportRow] = Field(default_factory=list)
    videos: list[StudyCohortMediaRow] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_examination_identity(self) -> StudyCohortCaseRow:
        examination_ids = [
            examination.patient_examination_id for examination in self.examinations
        ]
        case_hashes = [examination.case_hash for examination in self.examinations]
        if len(examination_ids) != len(set(examination_ids)):
            raise ValueError(
                "examinations must contain unique patient_examination_id values"
            )
        if self.patient_examination_ids != examination_ids:
            raise ValueError(
                "patient_examination_ids must match examinations in the same order"
            )
        if self.case_hashes != case_hashes:
            raise ValueError("case_hashes must match examinations in the same order")

        latest = self.examinations[0]
        if (
            self.patient_examination_id != latest.patient_examination_id
            or self.case_hash != latest.case_hash
            or self.examination_name != latest.examination_name
            or self.examination_date != latest.examination_date
        ):
            raise ValueError(
                "legacy examination fields must identify the first examination"
            )
        return self


__all__ = [
    "StudyCohortCaseRow",
    "StudyCohortExaminationRow",
    "StudyCohortMediaRow",
    "StudyCohortReportRow",
]
