from __future__ import annotations

import math
import re
from datetime import date, datetime, time
from functools import lru_cache
from pathlib import Path
from typing import Any, ClassVar, Mapping

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    field_validator,
    model_validator,
)


class ReportReaderFlags(BaseModel):
    """Typed configuration keys consumed by lx_anonymizer.report_reader.ReportReader."""

    model_config = ConfigDict(extra="allow")

    patient_info_line: str | None = None
    endoscope_info_line: str = ""
    examiner_info_line: str | None = None
    cut_off_below: list[str] = Field(default_factory=list)
    cut_off_above: list[str] = Field(default_factory=list)

    @field_validator(
        "patient_info_line",
        "examiner_info_line",
        mode="before",
    )
    @classmethod
    def normalize_optional_string(cls, value: Any) -> str | None:
        if value is None:
            return None
        return str(value).strip()

    @field_validator("endoscope_info_line", mode="before")
    @classmethod
    def normalize_required_string(cls, value: Any) -> str:
        if value is None:
            return ""
        return str(value).strip()

    @field_validator("cut_off_below", "cut_off_above", mode="before")
    @classmethod
    def normalize_cutoff_markers(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [value.strip()] if value.strip() else []
        if isinstance(value, (list, tuple, set)):
            return [
                str(item).strip()
                for item in value
                if item is not None and str(item).strip()
            ]
        return [str(value).strip()] if str(value).strip() else []


class ReportPatientInfo(BaseModel):
    """Patient metadata shape returned by report-reader extraction helpers."""

    model_config = ConfigDict(extra="forbid")

    first_name: str | None = None
    last_name: str | None = None
    dob: date | None = None
    casenumber: str | None = None
    gender: str | None = None

    @field_validator("first_name", "last_name", "casenumber", "gender", mode="before")
    @classmethod
    def normalize_string(cls, value: Any) -> str | None:
        return _normalize_optional_string(value)

    @field_validator("dob", mode="before")
    @classmethod
    def normalize_dob(cls, value: Any) -> date | None:
        return _parse_date_like(value)


class ReportExaminerInfo(BaseModel):
    """Examiner keys merged into report metadata."""

    model_config = ConfigDict(extra="forbid")

    examiner_first_name: str | None = None
    examiner_last_name: str | None = None

    @field_validator("examiner_first_name", "examiner_last_name", mode="before")
    @classmethod
    def normalize_string(cls, value: Any) -> str | None:
        return _normalize_optional_string(value)


class ReportExaminationInfo(BaseModel):
    """Examination date/time keys merged into report metadata."""

    model_config = ConfigDict(extra="forbid")

    examination_date: date | None = None
    examination_time: time | None = None

    @field_validator("examination_date", mode="before")
    @classmethod
    def normalize_examination_date(cls, value: Any) -> date | None:
        return _parse_date_like(value)

    @field_validator("examination_time", mode="before")
    @classmethod
    def normalize_examination_time(cls, value: Any) -> time | None:
        return _parse_time_like(value)


class ReportEndoscopeInfo(BaseModel):
    """Endoscope keys merged into report metadata."""

    model_config = ConfigDict(extra="forbid")

    endoscope_type: str | None = None
    endoscope_sn: str | None = None

    @field_validator("endoscope_type", "endoscope_sn", mode="before")
    @classmethod
    def normalize_string(cls, value: Any) -> str | None:
        return _normalize_optional_string(value)


class ReportRedactionSummary(BaseModel):
    """Summary payload stored under report_meta['redaction_summary']."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = "1.0"
    page_count: int = 0
    redaction_region_count: int = 0
    detector_sources: list[str] = Field(default_factory=list)
    confidence_min: float | None = None
    confidence_max: float | None = None
    confidence_mean: float | None = None

    @field_validator("page_count", "redaction_region_count", mode="before")
    @classmethod
    def normalize_non_negative_int(cls, value: Any) -> int:
        if value in (None, ""):
            return 0
        parsed = int(value)
        if parsed < 0:
            raise ValueError("count values must be >= 0")
        return parsed

    @field_validator("detector_sources", mode="before")
    @classmethod
    def normalize_detector_sources(cls, value: Any) -> list[str]:
        return _normalize_string_list(value)

    @field_validator(
        "confidence_min", "confidence_max", "confidence_mean", mode="before"
    )
    @classmethod
    def normalize_confidence(cls, value: Any) -> float | None:
        if value in (None, ""):
            return None
        parsed = float(value)
        if math.isnan(parsed):
            return None
        if parsed < 0 or parsed > 1:
            raise ValueError("confidence values must be within [0, 1]")
        return parsed


class ReportAnonymizerProvenance(BaseModel):
    """Provenance payload stored under report_meta['anonymizer_provenance']."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = "1.0"
    anonymizer_version: str = "unknown"
    detector_sources: list[str] = Field(default_factory=list)
    model_names: list[str] = Field(default_factory=list)
    model_versions: dict[str, str] = Field(default_factory=dict)
    proposal_counts: dict[str, int] = Field(default_factory=dict)

    @field_validator("detector_sources", "model_names", mode="before")
    @classmethod
    def normalize_string_lists(cls, value: Any) -> list[str]:
        return _normalize_string_list(value)

    @field_validator("model_versions", mode="before")
    @classmethod
    def normalize_model_versions(cls, value: Any) -> dict[str, str]:
        if value is None:
            return {}
        if not isinstance(value, Mapping):
            raise TypeError("model_versions must be a mapping")
        return {str(key): str(item) for key, item in value.items()}

    @field_validator("proposal_counts", mode="before")
    @classmethod
    def normalize_proposal_counts(cls, value: Any) -> dict[str, int]:
        if value is None:
            return {}
        if not isinstance(value, Mapping):
            raise TypeError("proposal_counts must be a mapping")
        counts: dict[str, int] = {}
        for key, item in value.items():
            parsed = int(item)
            if parsed < 0:
                raise ValueError("proposal count values must be >= 0")
            counts[str(key)] = parsed
        return counts


class ReportCropInfo(BaseModel):
    """Cropping metadata appended by process_report_with_cropping."""

    model_config = ConfigDict(extra="allow")

    cropped_regions: dict[str, list[Any]] = Field(default_factory=dict)
    cropping_enabled: bool = False
    total_cropped_regions: int = 0
    anonymized_pdf_error: str | None = None

    @field_validator("cropped_regions", mode="before")
    @classmethod
    def normalize_cropped_regions(cls, value: Any) -> dict[str, list[Any]]:
        if value is None:
            return {}
        if not isinstance(value, Mapping):
            raise TypeError("cropped_regions must be a mapping")
        normalized: dict[str, list[Any]] = {}
        for key, item in value.items():
            normalized[str(key)] = item if isinstance(item, list) else [item]
        return normalized

    @field_validator("total_cropped_regions", mode="before")
    @classmethod
    def normalize_total_cropped_regions(cls, value: Any) -> int:
        if value in (None, ""):
            return 0
        parsed = int(value)
        if parsed < 0:
            raise ValueError("total_cropped_regions must be >= 0")
        return parsed

    @field_validator("anonymized_pdf_error", mode="before")
    @classmethod
    def normalize_error(cls, value: Any) -> str | None:
        return _normalize_optional_string(value)


class ReportMeta(BaseModel):
    """Strong model for string-keyed report metadata produced by ReportReader."""

    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)

    _LEGACY_FIELD_ALIASES: ClassVar[dict[str, str]] = {
        "birth_date": "dob",
        "doctor_first_name": "examiner_first_name",
        "doctor_last_name": "examiner_last_name",
        "hospital": "center",
        "patient_first_name": "first_name",
        "patient_last_name": "last_name",
        "patient_dob": "dob",
        "patient_gender_name": "gender",
    }

    file_path: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    dob: date | None = None
    casenumber: str | None = None
    gender: str | None = None
    examination_date: date | None = None
    examination_time: time | None = None
    examiner_first_name: str | None = None
    examiner_last_name: str | None = None
    center: str | None = None
    endoscope_type: str | None = None
    endoscope_sn: str | None = None
    pdf_hash: str | None = None
    anonymized_pdf_path: str | Path | None = None
    redaction_summary: ReportRedactionSummary | None = None
    anonymizer_provenance: ReportAnonymizerProvenance | None = None
    text: str | None = None
    anonymized_text: str | None = None
    cropped_regions: dict[str, list[Any]] = Field(default_factory=dict)
    cropping_enabled: bool = False
    total_cropped_regions: int = 0
    anonymized_pdf_error: str | None = None

    @model_validator(mode="before")
    @classmethod
    def normalize_aliases(cls, data: Any) -> Any:
        if not isinstance(data, Mapping):
            return data

        normalized: dict[str, Any] = {}
        for raw_key, raw_value in data.items():
            key = cls._LEGACY_FIELD_ALIASES.get(str(raw_key), str(raw_key))
            if key not in cls.model_fields:
                raise ValueError(f"unknown ReportMeta key: {raw_key}")
            if key in normalized and _has_signal(normalized[key]):
                continue
            normalized[key] = raw_value
        return normalized

    @field_validator(
        "file_path",
        "first_name",
        "last_name",
        "casenumber",
        "gender",
        "examiner_first_name",
        "examiner_last_name",
        "center",
        "endoscope_type",
        "endoscope_sn",
        "pdf_hash",
        "text",
        "anonymized_text",
        "anonymized_pdf_error",
        mode="before",
    )
    @classmethod
    def normalize_optional_strings(cls, value: Any) -> str | None:
        return _normalize_optional_string(value)

    @field_validator("dob", "examination_date", mode="before")
    @classmethod
    def normalize_dates(cls, value: Any) -> date | None:
        return _parse_date_like(value)

    @field_validator("examination_time", mode="before")
    @classmethod
    def normalize_time(cls, value: Any) -> time | None:
        return _parse_time_like(value)

    @field_validator("pdf_hash")
    @classmethod
    def validate_pdf_hash(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if len(value) != 64 or any(
            ch not in "0123456789abcdef" for ch in value.lower()
        ):
            raise ValueError("pdf_hash must contain 64 hex chars")
        return value.lower()

    @field_validator("anonymized_pdf_path", mode="before")
    @classmethod
    def normalize_anonymized_pdf_path(cls, value: Any) -> str | Path | None:
        if value in (None, ""):
            return None
        if isinstance(value, Path):
            return value
        return str(value).strip() or None

    @field_validator("cropped_regions", mode="before")
    @classmethod
    def normalize_cropped_regions(cls, value: Any) -> dict[str, list[Any]]:
        return ReportCropInfo(cropped_regions=value).cropped_regions

    @field_validator("total_cropped_regions", mode="before")
    @classmethod
    def normalize_total_cropped_regions(cls, value: Any) -> int:
        return ReportCropInfo(total_cropped_regions=value).total_cropped_regions

    def to_report_reader_dict(self) -> dict[str, Any]:
        """Return a plain dict compatible with the existing ReportReader call sites."""

        payload = self.model_dump(mode="json", exclude_none=True)
        explicit_nulls = {
            field_name: None
            for field_name in self.__pydantic_fields_set__
            if getattr(self, field_name) is None
        }
        return payload | explicit_nulls


class ReportProcessRequest(BaseModel):
    """Typed inputs for ReportReader.process_report."""

    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)

    pdf_path: Path | None = None
    image_path: Path | None = None
    use_ensemble: StrictBool = False
    verbose: StrictBool = True
    use_llm: StrictBool | None = None
    text: str | None = None
    create_anonymized_pdf: StrictBool = False
    anonymized_pdf_output_path: str | Path | None = None

    @field_validator("pdf_path", "image_path", mode="before")
    @classmethod
    def normalize_optional_path(cls, value: Any) -> Path | None:
        if value in (None, ""):
            return None
        return Path(value)

    @field_validator("anonymized_pdf_output_path", mode="before")
    @classmethod
    def normalize_optional_output_path(cls, value: Any) -> str | Path | None:
        if value in (None, ""):
            return None
        if isinstance(value, Path):
            return value
        return str(value)

    @field_validator("text", mode="before")
    @classmethod
    def normalize_optional_text(cls, value: Any) -> str | None:
        if value is None:
            return None
        return str(value)

    @model_validator(mode="after")
    def validate_source(self) -> "ReportProcessRequest":
        if self.text is None and self.pdf_path is None and self.image_path is None:
            raise ValueError("Either pdf_path, image_path, or text must be provided")
        return self


class ReportProcessResult(BaseModel):
    """Typed output from ReportReader.process_report."""

    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)

    text: str
    anonymized_text: str
    report_meta: dict[str, Any]
    anonymized_pdf_path: Path | None = None

    def as_tuple(self) -> tuple[str, str, dict[str, Any], Path | None]:
        return (
            self.text,
            self.anonymized_text,
            self.report_meta,
            self.anonymized_pdf_path,
        )


class ReportCroppingRequest(BaseModel):
    """Typed inputs for ReportReader.process_report_with_cropping."""

    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)

    pdf_path: Path | None = None
    image_path: Path | None = None
    use_ensemble: StrictBool = False
    verbose: StrictBool = True
    use_llm: StrictBool | None = None
    text: str | None = None
    crop_output_dir: Path | None = None
    crop_sensitive_regions: StrictBool = True
    anonymization_output_dir: Path | None = None

    @field_validator(
        "pdf_path",
        "image_path",
        "crop_output_dir",
        "anonymization_output_dir",
        mode="before",
    )
    @classmethod
    def normalize_optional_path(cls, value: Any) -> Path | None:
        if value in (None, ""):
            return None
        return Path(value)

    @field_validator("text", mode="before")
    @classmethod
    def normalize_optional_text(cls, value: Any) -> str | None:
        if value is None:
            return None
        return str(value)

    def process_request(self) -> ReportProcessRequest:
        return ReportProcessRequest(
            pdf_path=self.pdf_path,
            image_path=self.image_path,
            use_ensemble=self.use_ensemble,
            verbose=self.verbose,
            use_llm=self.use_llm,
            text=self.text,
        )


_NULL_STRINGS = {"", "-", "n/a", "na", "none", "null", "undefined", "unknown"}
_DATE_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"^\d{4}-\d{2}-\d{2}$"), "%Y-%m-%d"),
    (re.compile(r"^\d{2}\.\d{2}\.\d{4}$"), "%d.%m.%Y"),
    (re.compile(r"^\d{2}\.\d{2}\.\d{2}$"), "%d.%m.%y"),
    (re.compile(r"^\d{2}/\d{2}/\d{4}$"), "%d/%m/%Y"),
    (re.compile(r"^\d{2}-\d{2}-\d{4}$"), "%d-%m-%Y"),
    (re.compile(r"^\d{4}/\d{2}/\d{2}$"), "%Y/%m/%d"),
)


def _normalize_optional_string(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    stripped = str(value).strip()
    if stripped.casefold() in _NULL_STRINGS:
        return None
    return stripped


def _normalize_string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if isinstance(value, (list, tuple, set)):
        return [
            str(item).strip()
            for item in value
            if item is not None and str(item).strip()
        ]
    return [str(value).strip()] if str(value).strip() else []


def _has_signal(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip().casefold() not in _NULL_STRINGS
    if isinstance(value, (list, dict, set, tuple)):
        return len(value) > 0
    return True


def _parse_date_like(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    if stripped.casefold() in _NULL_STRINGS:
        return None
    return _parse_date_like_cached(stripped)


@lru_cache(maxsize=4096)
def _parse_date_like_cached(value: str) -> date | None:
    for pattern, date_format in _DATE_PATTERNS:
        if not pattern.match(value):
            continue
        if date_format == "%Y-%m-%d":
            try:
                return date.fromisoformat(value)
            except ValueError:
                return None
        try:
            return datetime.strptime(value, date_format).date()
        except ValueError:
            return None
    return None


def _parse_time_like(value: Any) -> time | None:
    if value is None:
        return None
    if isinstance(value, time):
        return value
    if isinstance(value, datetime):
        return value.time().replace(microsecond=0)
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    if stripped.casefold() in _NULL_STRINGS:
        return None
    for time_format in ("%H:%M:%S", "%H:%M"):
        try:
            return datetime.strptime(stripped, time_format).time()
        except ValueError:
            continue
    return None


__all__ = [
    "ReportAnonymizerProvenance",
    "ReportCropInfo",
    "ReportEndoscopeInfo",
    "ReportExaminerInfo",
    "ReportExaminationInfo",
    "ReportMeta",
    "ReportPatientInfo",
    "ReportProcessRequest",
    "ReportProcessResult",
    "ReportCroppingRequest",
    "ReportReaderFlags",
    "ReportRedactionSummary",
]
