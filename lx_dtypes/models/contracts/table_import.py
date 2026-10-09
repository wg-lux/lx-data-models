"""Portable, data-only column mappings and validated study import records."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date
from typing import Annotated, Literal, Protocol, Self, cast
from uuid import UUID

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, model_validator

from .dtypes_record_persistence import DtypesRecordPersistencePayload
from .knowledge_base import KnowledgeBaseIdentity
from lx_dtypes.models.meta.ReportMeta import ReportPatientInfo


class TableColumn(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    columns: list[str] = Field(default_factory=list, max_length=100)
    value: str | None = None
    separator: str = "\n"
    extractor: str | None = Field(default=None, pattern=r"^[a-z][a-z0-9_]*$")
    output: str | None = None
    values: dict[str, str] = Field(default_factory=dict)
    date_format: str | None = None
    required: bool = True

    @model_validator(mode="after")
    def valid_source(self) -> Self:
        if bool(self.columns) == (self.value is not None):
            raise ValueError("Specify either columns or a constant value")
        if len(set(self.columns)) != len(self.columns) or any(
            not name.strip() for name in self.columns
        ):
            raise ValueError("Column names must be nonempty and unique")
        if (self.extractor is None) != (self.output is None):
            raise ValueError("extractor and output must be supplied together")
        if self.value is not None and (self.extractor or self.date_format):
            raise ValueError("Constant values cannot use extractors or date formats")
        return self


def _column_shorthand(value: object) -> object:
    if isinstance(value, str):
        return {"columns": [value]}
    if isinstance(value, list):
        return {"columns": cast(list[object], value)}
    return value


ColumnMapping = Annotated[TableColumn, BeforeValidator(_column_shorthand)]


class TableFinding(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    finding: ColumnMapping
    classifications: dict[str, ColumnMapping] = Field(default_factory=dict)


class TableSource(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    delimiter: str = Field(default=",", min_length=1, max_length=1)
    encoding: Literal["utf-8-sig", "utf-8", "cp1252"] = "utf-8-sig"
    sheet: str | None = None
    header_row: int = Field(default=1, ge=1, le=100)


class TableMapping(BaseModel):
    """One row is one examination; named finding groups preserve lesion identity."""

    model_config = ConfigDict(extra="forbid", strict=True)

    schema_version: Literal["1.0"] = "1.0"
    mapping_id: UUID = Field(strict=False)
    name: str = Field(min_length=1, max_length=255)
    knowledge_base: KnowledgeBaseIdentity
    source: TableSource = Field(default_factory=TableSource)
    row_id: ColumnMapping
    first_name: ColumnMapping
    last_name: ColumnMapping
    dob: ColumnMapping
    gender: ColumnMapping
    examination_date: ColumnMapping
    examination: ColumnMapping
    finding: ColumnMapping | None = None
    findings: dict[str, TableFinding] = Field(default_factory=dict, max_length=100)

    @model_validator(mode="after")
    def complete_identity(self) -> Self:
        for column in (
            self.row_id,
            self.first_name,
            self.last_name,
            self.dob,
            self.gender,
            self.examination_date,
            self.examination,
        ):
            if not column.required:
                raise ValueError("Identity and examination columns must be required")
        if "finding" in self.findings and self.finding is not None:
            raise ValueError("The finding group name is reserved by the shorthand")
        if any(not name.strip() for name in self.findings):
            raise ValueError("Finding group names must be nonempty")
        return self

    def finding_groups(self) -> dict[str, TableFinding]:
        groups = dict(self.findings)
        if self.finding is not None:
            groups["finding"] = TableFinding(finding=self.finding)
        return groups


class TableRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    row_number: int = Field(ge=1)
    source_id: UUID
    patient: ReportPatientInfo
    examination_date: date
    record: DtypesRecordPersistencePayload

    @model_validator(mode="after")
    def full_patient_identity(self) -> Self:
        missing = {"", "unknown", "unbekannt", "none", "null", "n/a"}
        if (
            any(
                value is None or value.strip().casefold() in missing
                for value in (self.patient.first_name, self.patient.last_name)
            )
            or self.patient.dob is None
            or self.patient.dob == date(1900, 1, 1)
        ):
            raise ValueError(
                "Complete patient identity and explicit gender are required"
            )
        if not self.patient.gender or len(self.patient.gender) > 255:
            raise ValueError("Explicit gender terminology is required")
        if any(
            len(value or "") > 255
            for value in (self.patient.first_name, self.patient.last_name)
        ):
            raise ValueError("Patient names exceed the supported length")
        if self.patient.dob > self.examination_date:
            raise ValueError("Birth date must not follow examination date")
        return self


class TableImportReceiptPayload(BaseModel):
    """No original names or source cells are retained in import receipts."""

    model_config = ConfigDict(extra="forbid")

    patient_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    examination_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    record: DtypesRecordPersistencePayload


class TableImportResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    row_count: int
    created_count: int
    replayed_count: int
    patient_examination_ids: list[int]
    matched_video_count: int
    matched_report_count: int
    dry_run: bool


class TableExtractionError(ValueError):
    """Safe diagnostics: source values and extractor exceptions never enter HTTP errors."""

    def __init__(self, row_number: int, field: str, code: str) -> None:
        self.row_number = row_number
        self.field = field
        self.code = code
        super().__init__(f"Row {row_number}, field {field}: {code}")


# Extractors are supplied by trusted Python callers, never imported by YAML.
class TableExtractor(Protocol):
    def __call__(self, text: str) -> Mapping[str, object]: ...
