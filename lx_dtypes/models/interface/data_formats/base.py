"""Syntax table of the structured text formats used for import and export.

Each format is identified by a stable :class:`DataFormatId` and maps every
:class:`SyntaxRole` it supports to its literal token. Roles a format does not
have (for example comments in JSON) are absent rather than empty, so callers
must handle unsupported syntax explicitly. Python tuples have no distinct
syntax in these formats and are written with the sequence tokens. Binary
formats such as Excel workbooks have no text tokens; tabular formats hold one
record per row with one column per top-level field.
"""

from collections.abc import Mapping
from enum import StrEnum
from types import MappingProxyType

import pandas as pd
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_serializer,
    field_validator,
    model_validator,
)


class DataFormatId(StrEnum):
    JSON = "json"
    YAML = "yaml"
    TOML = "toml"
    XML = "xml"
    FHIR_JSON = "fhir_json"
    FHIR_XML = "fhir_xml"
    CSV = "csv"
    TSV = "tsv"
    XLSX = "xlsx"


class SyntaxRole(StrEnum):
    KEY_VALUE_SEPARATOR = "key_value_separator"
    ITEM_SEPARATOR = "item_separator"
    MAPPING_OPEN = "mapping_open"
    MAPPING_CLOSE = "mapping_close"
    SEQUENCE_OPEN = "sequence_open"
    SEQUENCE_CLOSE = "sequence_close"
    SEQUENCE_ITEM = "sequence_item"
    TABLE_HEADER_OPEN = "table_header_open"
    TABLE_HEADER_CLOSE = "table_header_close"
    STRING_QUOTE = "string_quote"
    ESCAPE = "escape"
    COMMENT = "comment"
    COMMENT_OPEN = "comment_open"
    COMMENT_CLOSE = "comment_close"
    DOCUMENT_START = "document_start"
    DOCUMENT_END = "document_end"
    DECLARATION = "declaration"
    ELEMENT_OPEN = "element_open"
    ELEMENT_CLOSE = "element_close"
    END_TAG_OPEN = "end_tag_open"
    EMPTY_ELEMENT_CLOSE = "empty_element_close"
    ATTRIBUTE_VALUE_SEPARATOR = "attribute_value_separator"
    CDATA_OPEN = "cdata_open"
    CDATA_CLOSE = "cdata_close"
    FIELD_SEPARATOR = "field_separator"
    RECORD_SEPARATOR = "record_separator"
    NULL = "null"
    TRUE = "true"
    FALSE = "false"
    RESOURCE_TYPE_KEY = "resource_type_key"
    VALUE_ATTRIBUTE = "value_attribute"
    NAMESPACE = "namespace"


class DataFormat(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    identifier: DataFormatId
    media_type: str = Field(pattern=r"^[a-z]+/[a-z0-9.+-]+$")
    file_extensions: tuple[str, ...] = Field(min_length=1)
    base_format: DataFormatId | None = None
    binary: bool = False
    tabular: bool = False
    tokens: Mapping[SyntaxRole, str] = Field(default_factory=dict)

    @field_validator("file_extensions")
    @classmethod
    def _validate_extensions(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        for extension in value:
            if not extension.startswith(".") or extension != extension.lower():
                raise ValueError(
                    f"File extension must be lowercase and dotted: {extension!r}"
                )
        if len(set(value)) != len(value):
            raise ValueError("File extensions must be unique")
        return value

    @field_validator("tokens")
    @classmethod
    def _validate_tokens(
        cls, value: Mapping[SyntaxRole, str]
    ) -> Mapping[SyntaxRole, str]:
        for role, token in value.items():
            if token == "":
                raise ValueError(
                    f"Token for {role} must not be empty; omit unsupported roles"
                )
        return MappingProxyType(dict(value))

    @field_serializer("tokens")
    def _serialize_tokens(
        self, value: Mapping[SyntaxRole, str]
    ) -> dict[SyntaxRole, str]:
        return dict(value)

    @model_validator(mode="after")
    def _validate_base_format(self) -> "DataFormat":
        if self.base_format == self.identifier:
            raise ValueError("A format cannot be its own base format")
        if self.binary == bool(self.tokens):
            raise ValueError(
                "Text formats require syntax tokens and binary formats have none"
            )
        return self

    def supports(self, role: SyntaxRole) -> bool:
        return role in self.tokens

    def token(self, role: SyntaxRole) -> str:
        try:
            return self.tokens[role]
        except KeyError as exc:
            raise ValueError(f"{self.identifier} has no syntax for {role}") from exc


def _derive(base: DataFormat, **overrides: str) -> dict[SyntaxRole, str]:
    return {
        **base.tokens,
        **{SyntaxRole(role): token for role, token in overrides.items()},
    }


JSON_FORMAT = DataFormat(
    identifier=DataFormatId.JSON,
    media_type="application/json",
    file_extensions=(".json",),
    tokens={
        SyntaxRole.KEY_VALUE_SEPARATOR: ":",
        SyntaxRole.ITEM_SEPARATOR: ",",
        SyntaxRole.MAPPING_OPEN: "{",
        SyntaxRole.MAPPING_CLOSE: "}",
        SyntaxRole.SEQUENCE_OPEN: "[",
        SyntaxRole.SEQUENCE_CLOSE: "]",
        SyntaxRole.STRING_QUOTE: '"',
        SyntaxRole.ESCAPE: "\\",
        SyntaxRole.NULL: "null",
        SyntaxRole.TRUE: "true",
        SyntaxRole.FALSE: "false",
    },
)

YAML_FORMAT = DataFormat(
    identifier=DataFormatId.YAML,
    media_type="application/yaml",
    file_extensions=(".yaml", ".yml"),
    tokens={
        # Flow-style collections share JSON brackets; block style uses SEQUENCE_ITEM.
        SyntaxRole.KEY_VALUE_SEPARATOR: ": ",
        SyntaxRole.ITEM_SEPARATOR: ", ",
        SyntaxRole.MAPPING_OPEN: "{",
        SyntaxRole.MAPPING_CLOSE: "}",
        SyntaxRole.SEQUENCE_OPEN: "[",
        SyntaxRole.SEQUENCE_CLOSE: "]",
        SyntaxRole.SEQUENCE_ITEM: "- ",
        SyntaxRole.STRING_QUOTE: '"',
        SyntaxRole.ESCAPE: "\\",
        SyntaxRole.COMMENT: "#",
        SyntaxRole.DOCUMENT_START: "---",
        SyntaxRole.DOCUMENT_END: "...",
        SyntaxRole.NULL: "null",
        SyntaxRole.TRUE: "true",
        SyntaxRole.FALSE: "false",
    },
)

TOML_FORMAT = DataFormat(
    identifier=DataFormatId.TOML,
    media_type="application/toml",
    file_extensions=(".toml",),
    tokens={
        # TOML has no null; absent keys represent missing values.
        SyntaxRole.KEY_VALUE_SEPARATOR: " = ",
        SyntaxRole.ITEM_SEPARATOR: ", ",
        SyntaxRole.MAPPING_OPEN: "{",
        SyntaxRole.MAPPING_CLOSE: "}",
        SyntaxRole.SEQUENCE_OPEN: "[",
        SyntaxRole.SEQUENCE_CLOSE: "]",
        SyntaxRole.TABLE_HEADER_OPEN: "[",
        SyntaxRole.TABLE_HEADER_CLOSE: "]",
        SyntaxRole.STRING_QUOTE: '"',
        SyntaxRole.ESCAPE: "\\",
        SyntaxRole.COMMENT: "#",
        SyntaxRole.TRUE: "true",
        SyntaxRole.FALSE: "false",
    },
)

XML_FORMAT = DataFormat(
    identifier=DataFormatId.XML,
    media_type="application/xml",
    file_extensions=(".xml",),
    tokens={
        SyntaxRole.DECLARATION: '<?xml version="1.0" encoding="UTF-8"?>',
        SyntaxRole.ELEMENT_OPEN: "<",
        SyntaxRole.ELEMENT_CLOSE: ">",
        SyntaxRole.END_TAG_OPEN: "</",
        SyntaxRole.EMPTY_ELEMENT_CLOSE: "/>",
        SyntaxRole.ATTRIBUTE_VALUE_SEPARATOR: "=",
        SyntaxRole.STRING_QUOTE: '"',
        SyntaxRole.ESCAPE: "&",
        SyntaxRole.COMMENT_OPEN: "<!--",
        SyntaxRole.COMMENT_CLOSE: "-->",
        SyntaxRole.CDATA_OPEN: "<![CDATA[",
        SyntaxRole.CDATA_CLOSE: "]]>",
    },
)

FHIR_JSON_FORMAT = DataFormat(
    identifier=DataFormatId.FHIR_JSON,
    media_type="application/fhir+json",
    file_extensions=(".fhir.json",),
    base_format=DataFormatId.JSON,
    tokens=_derive(JSON_FORMAT, resource_type_key="resourceType"),
)

FHIR_XML_FORMAT = DataFormat(
    identifier=DataFormatId.FHIR_XML,
    media_type="application/fhir+xml",
    file_extensions=(".fhir.xml",),
    base_format=DataFormatId.XML,
    # FHIR XML carries primitive values in a "value" attribute; the resource
    # type is the root element name, so there is no resource type key.
    tokens=_derive(
        XML_FORMAT, value_attribute="value", namespace="http://hl7.org/fhir"
    ),
)

CSV_FORMAT = DataFormat(
    identifier=DataFormatId.CSV,
    media_type="text/csv",
    file_extensions=(".csv",),
    tabular=True,
    tokens={
        SyntaxRole.FIELD_SEPARATOR: ",",
        SyntaxRole.RECORD_SEPARATOR: "\r\n",
        SyntaxRole.STRING_QUOTE: '"',
        SyntaxRole.ESCAPE: '"',
    },
)

TSV_FORMAT = DataFormat(
    identifier=DataFormatId.TSV,
    media_type="text/tab-separated-values",
    file_extensions=(".tsv",),
    tabular=True,
    # IANA TSV has no quoting, so fields cannot contain tabs or line breaks.
    tokens={
        SyntaxRole.FIELD_SEPARATOR: "\t",
        SyntaxRole.RECORD_SEPARATOR: "\n",
    },
)

XLSX_FORMAT = DataFormat(
    identifier=DataFormatId.XLSX,
    media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    file_extensions=(".xlsx",),
    binary=True,
    tabular=True,
)

DATA_FORMATS: Mapping[DataFormatId, DataFormat] = MappingProxyType(
    {
        data_format.identifier: data_format
        for data_format in (
            JSON_FORMAT,
            YAML_FORMAT,
            TOML_FORMAT,
            XML_FORMAT,
            FHIR_JSON_FORMAT,
            FHIR_XML_FORMAT,
            CSV_FORMAT,
            TSV_FORMAT,
            XLSX_FORMAT,
        )
    }
)


def get_data_format(identifier: DataFormatId | str) -> DataFormat:
    try:
        return DATA_FORMATS[DataFormatId(identifier)]
    except ValueError as exc:
        raise ValueError(f"Unknown data format: {identifier!r}") from exc


def data_format_for_media_type(media_type: str) -> DataFormat:
    normalized = media_type.split(";", 1)[0].strip().lower()
    for data_format in DATA_FORMATS.values():
        if data_format.media_type == normalized:
            return data_format
    raise ValueError(f"Unknown media type: {media_type!r}")


def data_format_for_filename(filename: str) -> DataFormat:
    # Longest suffix wins so ".fhir.json" is not resolved as plain JSON.
    lowered = filename.lower()
    matches = [
        (len(extension), data_format)
        for data_format in DATA_FORMATS.values()
        for extension in data_format.file_extensions
        if lowered.endswith(extension)
    ]
    if not matches:
        raise ValueError(f"No data format for file: {filename!r}")
    return max(matches, key=lambda match: match[0])[1]


def syntax_table() -> pd.DataFrame:
    """Return formats as rows and syntax roles as columns; unsupported roles are NA."""
    rows = {
        identifier.value: {
            role.value: data_format.tokens.get(role) for role in SyntaxRole
        }
        for identifier, data_format in DATA_FORMATS.items()
    }
    return pd.DataFrame.from_dict(rows, orient="index", dtype="string")
