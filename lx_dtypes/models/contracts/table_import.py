"""Portable, data-only column mappings and validated study import records."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from datetime import date
from typing import Annotated, Literal, Protocol, Self, cast
from uuid import UUID

from pydantic import BeforeValidator, Field, model_validator

from lx_dtypes.models.descriptor_value import DescriptorValue
from lx_dtypes.models.knowledge_base.classification_choice_descriptor.ClassificationChoiceDescriptor import (
    ClassificationChoiceDescriptor,
)
from lx_dtypes.models.knowledge_base.pydantic_main import KB_MODEL_NAMES_LITERAL
from lx_dtypes.models.meta.ReportMeta import ReportPatientInfo
from lx_dtypes.models.model import DtypesModel, FrozenContractModel, StrictContractModel

from .dtypes_record_persistence import DtypesRecordPersistencePayload
from .knowledge_base import KnowledgeBaseIdentity


class TableColumn(FrozenContractModel):
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


TableField = Literal[
    "row_id",
    "first_name",
    "last_name",
    "dob",
    "gender",
    "examination_date",
    "examination",
    "finding",
]


class TableFieldVocabulary(StrictContractModel):
    """Header suggestions and exact source-value translations for one field."""

    aliases: list[str] = Field(min_length=1)
    values: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def valid_terms(self) -> Self:
        normalized = [alias.strip().casefold() for alias in self.aliases]
        if not all(normalized) or len(set(normalized)) != len(normalized):
            raise ValueError("Header aliases must be nonempty and distinct")
        if any(
            not key.strip() or not value.strip() for key, value in self.values.items()
        ):
            raise ValueError("Value translations must be nonempty")
        return self


class TableConceptVocabulary(TableFieldVocabulary):
    """A candidate in an explicitly selected KB closure, not an approved mapping."""

    concept_type: KB_MODEL_NAMES_LITERAL
    name: str = Field(min_length=1)
    knowledge_base: KnowledgeBaseIdentity
    source_module: str = Field(min_length=1)


class TableImportVocabulary(StrictContractModel):
    """Reviewable suggestions; never an executable or complete TableMapping."""

    schema_version: Literal["1.0"]
    fields: dict[TableField, TableFieldVocabulary] = Field(min_length=1)
    concept_models: list[KB_MODEL_NAMES_LITERAL] = Field(default_factory=list)
    concept_aliases: dict[KB_MODEL_NAMES_LITERAL, dict[str, list[str]]] = Field(
        default_factory=dict
    )
    concepts: list[TableConceptVocabulary] = Field(default_factory=list)

    @model_validator(mode="after")
    def distinct_fields(self) -> Self:
        aliases = [
            alias.strip().casefold()
            for field in self.fields.values()
            for alias in field.aliases
        ]
        if len(set(aliases)) != len(aliases):
            raise ValueError("Header aliases must not identify multiple fields")
        if len(set(self.concept_models)) != len(self.concept_models):
            raise ValueError("Concept models must be unique")
        for concept_type, entries in self.concept_aliases.items():
            if concept_type not in self.concept_models:
                raise ValueError("Concept aliases require a selected concept model")
            for name, terms in entries.items():
                if not name.strip():
                    raise ValueError("Concept names must be nonempty")
                TableFieldVocabulary(aliases=terms)
        return self

    def suggest_concepts(
        self, term: str, *, concept_type: KB_MODEL_NAMES_LITERAL | None = None
    ) -> list[TableConceptVocabulary]:
        """Match identifiers/labels without guessing among shared clinical terms."""
        normalized = term.strip().casefold()
        return [
            concept
            for concept in self.concepts
            if (concept_type is None or concept.concept_type == concept_type)
            and normalized in {alias.strip().casefold() for alias in concept.aliases}
        ]

    def suggest_columns(self, columns: list[str]) -> dict[TableField, list[str]]:
        """Keep all matching original headers, including ambiguous candidates."""
        return {
            name: matches
            for name, field in self.fields.items()
            if (
                matches := [
                    column
                    for column in columns
                    if column.strip().casefold()
                    in {alias.strip().casefold() for alias in field.aliases}
                ]
            )
        }


class TableDescriptor(StrictContractModel):
    """Explicit source representation; the referenced KB owns admissible values."""

    column: ColumnMapping
    value_type: Literal["text", "integer", "number", "boolean", "selection"]

    def parse_value(
        self, value: str, descriptor: ClassificationChoiceDescriptor
    ) -> DescriptorValue:
        expected = {
            "text": "text",
            "integer": "numeric",
            "number": "numeric",
            "boolean": "boolean",
            "selection": "selection",
        }[self.value_type]
        if descriptor.classification_choice_descriptor_type.value != expected:
            raise ValueError("Mapping representation disagrees with KB descriptor type")
        parsed: DescriptorValue
        if self.value_type == "text":
            parsed = value
        elif self.value_type == "boolean":
            if value not in {"true", "false"}:
                raise ValueError("Boolean descriptor requires true or false")
            parsed = value == "true"
        elif self.value_type == "selection":
            try:
                selected: object = json.loads(value)
            except RecursionError as error:
                raise ValueError(
                    "Selection nesting exceeds supported JSON depth"
                ) from error
            if not isinstance(selected, list) or not all(
                isinstance(item, str) for item in selected
            ):
                raise ValueError("Selection requires a JSON array of strings")
            parsed = cast(list[str], selected)
        else:
            if (
                self.value_type == "integer"
                and re.fullmatch(r"[+-]?[0-9]+", value) is None
            ):
                raise ValueError(
                    "Integer descriptor requires an integral decimal value"
                )
            if (
                self.value_type == "number"
                and re.fullmatch(
                    r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?", value
                )
                is None
            ):
                raise ValueError("Number descriptor requires decimal numeric spelling")
            parsed = int(value) if self.value_type == "integer" else float(value)
        return descriptor.validate_value(parsed)


class TableClassification(StrictContractModel):
    choice: ColumnMapping
    descriptors: dict[str, TableDescriptor] = Field(
        default_factory=dict, max_length=100
    )


class TableFinding(StrictContractModel):
    finding: ColumnMapping
    classifications: dict[str, TableClassification | ColumnMapping] = Field(
        default_factory=dict
    )

    def classification_groups(self) -> dict[str, TableClassification]:
        return {
            name: item
            if isinstance(item, TableClassification)
            else TableClassification(choice=item)
            for name, item in self.classifications.items()
        }


class TableSource(StrictContractModel):
    delimiter: str = Field(default=",", min_length=1, max_length=1)
    encoding: Literal["utf-8-sig", "utf-8", "cp1252"] = "utf-8-sig"
    sheet: str | None = None
    header_row: int = Field(default=1, ge=1, le=100)


class TableMapping(StrictContractModel):
    """One row is one examination; named finding groups preserve lesion identity."""

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


class TableRecord(DtypesModel):
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


class TableImportReceiptPayload(DtypesModel):
    """No original names or source cells are retained in import receipts."""

    patient_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    examination_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    # Historical receipts predate the normalized gender terminology identifier.
    gender: str | None = Field(default=None, min_length=1, max_length=255)
    record: DtypesRecordPersistencePayload


class TableImportResult(DtypesModel):
    row_count: int
    created_count: int
    replayed_count: int
    patient_examination_ids: list[int]
    receipt_ids: list[int]
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
