from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from lx_dtypes.models import SensitiveMeta
from pydantic import BaseModel, ConfigDict, Field, field_validator


class ReportAnonymizationResult(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        extra="forbid",
        frozen=True,
        strict=True,
        str_strip_whitespace=False,
    )

    original_text: str
    anonymized_text: str
    extracted_metadata: SensitiveMeta = Field(default_factory=SensitiveMeta)
    anonymized_path: Path

    @field_validator("original_text", "anonymized_text", mode="before")
    @classmethod
    def normalize_text(cls, value: object) -> str:
        if value is None:
            return ""
        return str(value)

    @field_validator("extracted_metadata", mode="before")
    @classmethod
    def normalize_extracted_metadata(cls, value: object) -> SensitiveMeta:
        if isinstance(value, SensitiveMeta):
            return value
        return SensitiveMeta.from_dict(value if isinstance(value, dict) else None)

    @classmethod
    def from_process_report_result(
        cls,
        value: Sequence[object],
    ) -> "ReportAnonymizationResult":
        if len(value) != 4:
            raise ValueError("process_report result must contain exactly four values")
        original_text, anonymized_text, extracted_metadata, anonymized_path = value
        return cls.model_validate(
            {
                "original_text": original_text,
                "anonymized_text": anonymized_text,
                "extracted_metadata": extracted_metadata,
                "anonymized_path": anonymized_path,
            }
        )


__all__ = ["ReportAnonymizationResult"]
