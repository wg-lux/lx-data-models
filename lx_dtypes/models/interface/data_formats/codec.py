"""Validated import and export of Pydantic records in every registered data format.

Export dumps each record in JSON mode by alias. Import restores JSON values,
then validates every record through the target model's JSON validator, so
strict models accept ISO dates, enums and UUIDs exactly as they would from a
JSON API. Layouts per format:

* JSON and YAML: a list of record objects.
* TOML: an array of tables named ``records``; TOML has no null, so ``None``
  fields are omitted and ``None`` inside arrays is rejected.
* XML: ``<records><record><field name=... type=...>`` with explicit JSON types.
* FHIR JSON and FHIR XML: a ``collection`` Bundle with one entry per resource;
  a single resource of the model's ``resourceType`` is also accepted on import.
* CSV, TSV and XLSX: a header row of top-level fields and one row per record.
  Nested values are JSON text. An empty cell is null when the field allows it,
  an empty string for string fields, and otherwise absent so defaults apply.

TSV refuses tabs and line breaks in cells and XLSX refuses carriage returns
instead of altering text. Spreadsheet cells are exported literally, including text starting with ``=``;
hosts presenting files to spreadsheet users own any formula-injection policy.
"""

import csv
import io
import json
import os
import tomllib
from collections.abc import Callable, Hashable, Iterable
from datetime import date, datetime, time
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import cast

import tomli_w
import yaml
from openpyxl import Workbook, load_workbook
from pydantic import BaseModel, ValidationError

from lx_dtypes.models.interface.data_formats._markup import (
    MarkupError,
    dump_fhir_xml,
    dump_xml,
    dump_xml_record,
    load_fhir_xml,
    load_xml,
    load_xml_record,
)
from lx_dtypes.models.interface.data_formats._schema import JsonValue, SchemaCoercer

from .base import (
    DataFormat,
    DataFormatId,
    SyntaxRole,
    data_format_for_filename,
    get_data_format,
)

DEFAULT_MAX_BYTES = 64 * 1024 * 1024
_EXCEL_CELL_LIMIT = 32767
_EXCEL_EXACT_INTEGER = 10**15
_SHEET_NAME = "records"

type Record = dict[str, JsonValue]


class DataFormatError(ValueError):
    """Raised when content cannot be represented in, or read from, a data format.

    Messages never quote imported content, and imported-content failures are
    not chained to parser exceptions whose text or tracebacks could quote it.
    """


class RecordValidationError(DataFormatError):
    """Raised when readable content does not validate as the target model."""


def dump_records[M: BaseModel](
    model: type[M], records: Iterable[M], data_format: DataFormatId | str
) -> bytes:
    """Serialize records of exactly ``model`` into the given format."""
    selected = get_data_format(data_format)
    payloads = _payloads(model, records)
    try:
        return _dump(model, payloads, selected)
    except (MarkupError, ValueError, TypeError) as exc:
        if isinstance(exc, DataFormatError):
            raise
        raise DataFormatError(
            f"Cannot export {model.__name__} as {selected.identifier}: {exc}"
        ) from exc


def load_records[M: BaseModel](
    model: type[M],
    content: bytes,
    data_format: DataFormatId | str,
    *,
    max_bytes: int = DEFAULT_MAX_BYTES,
) -> list[M]:
    """Parse and validate records of ``model`` from bounded content."""
    selected = get_data_format(data_format)
    payloads = _parse(
        lambda: _load(model, _bounded(content, max_bytes), selected), selected
    )
    return [_validate(model, index, payload) for index, payload in enumerate(payloads)]


def dump_record[M: BaseModel](
    model: type[M], record: M, data_format: DataFormatId | str
) -> bytes:
    """Serialize one record as a single document, or a header and one row."""
    selected = get_data_format(data_format)
    (payload,) = _payloads(model, [record])
    try:
        return _dump_one(model, payload, selected)
    except (MarkupError, ValueError, TypeError) as exc:
        if isinstance(exc, DataFormatError):
            raise
        raise DataFormatError(
            f"Cannot export {model.__name__} as {selected.identifier}: {exc}"
        ) from exc


def load_record[M: BaseModel](
    model: type[M],
    content: bytes,
    data_format: DataFormatId | str,
    *,
    max_bytes: int = DEFAULT_MAX_BYTES,
) -> M:
    """Parse and validate one record from bounded content.

    JSON, YAML and TOML documents are the record mapping itself, XML is a
    ``<record>`` root, FHIR is a single resource and tabular content holds
    exactly one row under its header.
    """
    selected = get_data_format(data_format)
    payload = _parse(
        lambda: _load_one(model, _bounded(content, max_bytes), selected), selected
    )
    return _validate(model, 0, payload)


def write_records[M: BaseModel](
    model: type[M],
    records: Iterable[M],
    path: Path,
    *,
    data_format: DataFormatId | str | None = None,
    overwrite: bool = False,
) -> Path:
    """Export to ``path`` atomically; the format defaults to the file extension."""
    selected = _format_for(path, data_format)
    return _publish(
        dump_records(model, records, selected.identifier), path, overwrite=overwrite
    )


def write_record[M: BaseModel](
    model: type[M],
    record: M,
    path: Path,
    *,
    data_format: DataFormatId | str | None = None,
    overwrite: bool = False,
) -> Path:
    """Export one record to ``path`` atomically; see :func:`load_record` for layouts."""
    selected = _format_for(path, data_format)
    return _publish(
        dump_record(model, record, selected.identifier), path, overwrite=overwrite
    )


def _publish(content: bytes, path: Path, *, overwrite: bool) -> Path:
    destination = path.absolute()
    destination.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(
        prefix=".lx-export-", dir=destination.parent, delete=False
    ) as target:
        temporary_path = Path(target.name)
        target.write(content)
        target.flush()
        os.fsync(target.fileno())
    try:
        if overwrite:
            os.replace(temporary_path, destination)
        else:
            # Link publication is atomic and refuses an existing destination.
            try:
                os.link(temporary_path, destination)
            except FileExistsError:
                raise FileExistsError(
                    f"Export destination already exists: {destination}"
                ) from None
    finally:
        temporary_path.unlink(missing_ok=True)
    return destination


def read_records[M: BaseModel](
    model: type[M],
    path: Path,
    *,
    data_format: DataFormatId | str | None = None,
    max_bytes: int = DEFAULT_MAX_BYTES,
) -> list[M]:
    """Import from ``path``; the format defaults to the file extension."""
    selected = _format_for(path, data_format)
    return load_records(
        model, _read_bounded(path, max_bytes), selected.identifier, max_bytes=max_bytes
    )


def read_record[M: BaseModel](
    model: type[M],
    path: Path,
    *,
    data_format: DataFormatId | str | None = None,
    max_bytes: int = DEFAULT_MAX_BYTES,
) -> M:
    """Import one record from ``path``; the format defaults to the file extension."""
    selected = _format_for(path, data_format)
    return load_record(
        model, _read_bounded(path, max_bytes), selected.identifier, max_bytes=max_bytes
    )


def _read_bounded(path: Path, max_bytes: int) -> bytes:
    # Read one byte past the limit so oversized files fail without loading them whole.
    with path.open("rb") as source:
        return source.read(max_bytes + 1)


def _bounded(content: bytes, max_bytes: int) -> bytes:
    if len(content) > max_bytes:
        raise DataFormatError(f"Content exceeds the {max_bytes} byte import limit")
    return content


def _parse[T](load: Callable[[], T], data_format: DataFormat) -> T:
    try:
        return load()
    except DataFormatError:
        raise
    except yaml.MarkedYAMLError as exc:
        # PyYAML messages quote document lines; keep only the problem and position.
        mark = exc.problem_mark
        position = f" at line {mark.line + 1}, column {mark.column + 1}" if mark else ""
        raise DataFormatError(
            f"Cannot import {data_format.identifier} content: {exc.problem}{position}"
        ) from None
    except (MarkupError, ValueError, TypeError, KeyError, yaml.YAMLError) as exc:
        raise DataFormatError(
            f"Cannot import {data_format.identifier} content: {exc}"
        ) from None


def _payloads[M: BaseModel](model: type[M], records: Iterable[M]) -> list[Record]:
    payloads: list[Record] = []
    for index, record in enumerate(records):
        if type(record) is not model:
            raise DataFormatError(
                f"Record {index} is {type(record).__name__}, expected {model.__name__}"
            )
        payloads.append(cast(Record, record.model_dump(mode="json", by_alias=True)))
    return payloads


def _format_for(path: Path, data_format: DataFormatId | str | None) -> DataFormat:
    return (
        data_format_for_filename(path.name)
        if data_format is None
        else get_data_format(data_format)
    )


def _validate[M: BaseModel](model: type[M], index: int, payload: JsonValue) -> M:
    try:
        return model.model_validate_json(
            json.dumps(payload, ensure_ascii=False, allow_nan=False)
        )
    except ValidationError as exc:
        # Locations and messages only: imported values may be clinical data.
        details = "; ".join(
            f"{'.'.join(str(part) for part in error['loc']) or '<record>'}: {error['msg']}"
            for error in exc.errors(include_input=False, include_url=False)
        )
        raise RecordValidationError(
            f"Record {index} is not a valid {model.__name__}: {details}"
        ) from None


def _dump(
    model: type[BaseModel], payloads: list[Record], data_format: DataFormat
) -> bytes:
    match data_format.identifier:
        case DataFormatId.JSON:
            return _dump_json(cast(list[JsonValue], payloads), data_format)
        case DataFormatId.YAML:
            return yaml.safe_dump(
                payloads, allow_unicode=True, sort_keys=False, explicit_start=True
            ).encode("utf-8")
        case DataFormatId.TOML:
            records = [_without_null(payload) for payload in payloads]
            return tomli_w.dumps({_SHEET_NAME: records}).encode("utf-8")
        case DataFormatId.XML:
            return dump_xml(payloads)
        case DataFormatId.FHIR_JSON:
            return _dump_json(_bundle(payloads), data_format)
        case DataFormatId.FHIR_XML:
            return dump_fhir_xml(_bundle(payloads))
        case DataFormatId.CSV | DataFormatId.TSV:
            return _dump_delimited(_columns(model, payloads), payloads, data_format)
        case DataFormatId.XLSX:
            return _dump_xlsx(_columns(model, payloads), payloads)


def _dump_one(
    model: type[BaseModel], payload: Record, data_format: DataFormat
) -> bytes:
    match data_format.identifier:
        case DataFormatId.JSON:
            return _dump_json(payload, data_format)
        case DataFormatId.YAML:
            return yaml.safe_dump(
                payload, allow_unicode=True, sort_keys=False, explicit_start=True
            ).encode("utf-8")
        case DataFormatId.TOML:
            return tomli_w.dumps(_without_null(payload)).encode("utf-8")
        case DataFormatId.XML:
            return dump_xml_record(payload)
        case DataFormatId.FHIR_JSON:
            return _dump_json(_fhir_resource(0, payload), data_format)
        case DataFormatId.FHIR_XML:
            return dump_fhir_xml(_fhir_resource(0, payload))
        case DataFormatId.CSV | DataFormatId.TSV | DataFormatId.XLSX:
            return _dump(model, [payload], data_format)


def _load_one(
    model: type[BaseModel], content: bytes, data_format: DataFormat
) -> JsonValue:
    match data_format.identifier:
        case DataFormatId.JSON:
            return _require_mapping(_load_json(_text(content)))
        case DataFormatId.YAML:
            return _require_mapping(_load_yaml(_text(content)))
        case DataFormatId.TOML:
            return _require_mapping(_json_compatible(tomllib.loads(_text(content))))
        case DataFormatId.XML:
            return load_xml_record(content)
        case _:
            # FHIR resources and single tabular rows share the list readers.
            records = _load(model, content, data_format)
            if len(records) != 1:
                raise DataFormatError(
                    f"Expected exactly one record, found {len(records)}"
                )
            return records[0]


def _require_mapping(document: JsonValue) -> Record:
    if not isinstance(document, dict):
        raise DataFormatError("Content must be a single record mapping")
    return document


def _load(
    model: type[BaseModel], content: bytes, data_format: DataFormat
) -> list[JsonValue]:
    match data_format.identifier:
        case DataFormatId.JSON:
            return _require_list(_load_json(_text(content)))
        case DataFormatId.YAML:
            return _require_list(_load_yaml(_text(content)))
        case DataFormatId.TOML:
            document = _json_compatible(tomllib.loads(_text(content)))
            if not isinstance(document, dict) or set(document) - {_SHEET_NAME}:
                raise DataFormatError(
                    f"TOML content must contain only [[{_SHEET_NAME}]] tables"
                )
            return _require_list(document.get(_SHEET_NAME, []))
        case DataFormatId.XML:
            return list(load_xml(content))
        case DataFormatId.FHIR_JSON:
            document = _load_json(_text(content))
            if not isinstance(document, dict):
                raise DataFormatError("FHIR JSON content must be a resource object")
            return _resources(model, cast(Record, document))
        case DataFormatId.FHIR_XML:
            coercer = SchemaCoercer(model)
            return [
                coercer.coerce(resource, coercer.root, decode_nested=False)
                for resource in _resources(model, load_fhir_xml(content))
            ]
        case DataFormatId.CSV | DataFormatId.TSV:
            return _from_rows(model, _read_delimited(_text(content), data_format))
        case DataFormatId.XLSX:
            return _from_rows(model, _read_xlsx(content))


def _text(content: bytes) -> str:
    try:
        # Spreadsheet applications commonly prepend a byte-order mark.
        return content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise DataFormatError("Content is not valid UTF-8") from exc


def _dump_json(payload: JsonValue, data_format: DataFormat) -> bytes:
    separators = (
        data_format.token(SyntaxRole.ITEM_SEPARATOR),
        data_format.token(SyntaxRole.KEY_VALUE_SEPARATOR) + " ",
    )
    text = json.dumps(
        payload, ensure_ascii=False, allow_nan=False, indent=2, separators=separators
    )
    return (text + "\n").encode("utf-8")


def _require_list(document: JsonValue) -> list[JsonValue]:
    if not isinstance(document, list):
        raise DataFormatError("Content must be a list of records")
    return document


def _unique_object(pairs: list[tuple[str, JsonValue]]) -> Record:
    result: Record = {}
    for key, value in pairs:
        if key in result:
            # Parsers disagree on which duplicate wins, so the record is ambiguous.
            raise DataFormatError("JSON objects must not repeat keys")
        result[key] = value
    return result


def _load_json(text: str) -> JsonValue:
    return cast(JsonValue, json.loads(text, object_pairs_hook=_unique_object))


def _load_yaml(text: str) -> JsonValue:
    return _json_compatible(yaml.load(text, Loader=_StrictYamlLoader))


class _StrictYamlLoader(yaml.SafeLoader):
    """Reject aliases, which expand without bound once materialised, and repeated keys."""

    def compose_node(self, parent: yaml.Node | None, index: int) -> yaml.Node | None:  # type: ignore[override]
        if self.check_event(yaml.AliasEvent):
            raise DataFormatError("YAML aliases are not supported in imported records")
        return super().compose_node(parent, index)  # type: ignore[arg-type]

    def construct_mapping(
        self, node: yaml.MappingNode, deep: bool = False
    ) -> dict[Hashable, object]:
        keys: set[Hashable] = set()
        for key_node, _ in node.value:
            key = self.construct_object(key_node, deep=True)  # type: ignore[no-untyped-call]
            if key in keys:
                raise DataFormatError("YAML mappings must not repeat keys")
            keys.add(key)
        return super().construct_mapping(node, deep=deep)


def _json_compatible(value: object) -> JsonValue:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, list):
        return [_json_compatible(item) for item in cast(list[object], value)]
    if isinstance(value, dict):
        result: Record = {}
        for key, item in cast(dict[object, object], value).items():
            if not isinstance(key, str):
                raise DataFormatError(
                    f"Mapping keys must be strings, got {type(key).__name__}"
                )
            result[key] = _json_compatible(item)
        return result
    raise DataFormatError(f"Unsupported value type: {type(value).__name__}")


def _without_null(value: Record) -> Record:
    result: Record = {}
    for key, item in value.items():
        if item is None:
            continue
        result[key] = _without_null_item(item)
    return result


def _without_null_item(value: JsonValue) -> JsonValue:
    if isinstance(value, dict):
        return _without_null(value)
    if isinstance(value, list):
        if any(item is None for item in value):
            raise DataFormatError("TOML arrays cannot contain null values")
        return [_without_null_item(item) for item in value]
    return value


# FHIR


def _prune_fhir(value: JsonValue) -> JsonValue:
    # FHIR JSON forbids null and empty arrays or objects.
    if isinstance(value, dict):
        pruned = {key: _prune_fhir(item) for key, item in value.items()}
        return {key: item for key, item in pruned.items() if item not in (None, [], {})}
    if isinstance(value, list):
        return [_prune_fhir(item) for item in value]
    return value


def _fhir_resource(index: int, payload: Record) -> Record:
    if not isinstance(payload.get("resourceType"), str):
        raise DataFormatError(
            f"Record {index} has no resourceType and is not a FHIR resource"
        )
    return cast(Record, _prune_fhir(payload))


def _bundle(payloads: list[Record]) -> Record:
    entries: list[JsonValue] = [
        {"resource": _fhir_resource(index, payload)}
        for index, payload in enumerate(payloads)
    ]
    bundle: Record = {"resourceType": "Bundle", "type": "collection"}
    if entries:
        bundle["entry"] = entries
    return bundle


def _model_resource_type(model: type[BaseModel]) -> str:
    coercer = SchemaCoercer(model)
    schema = coercer.property_schema(coercer.root, "resourceType")
    const = schema.get("const")
    if isinstance(const, str):
        return const
    choices = schema.get("enum")
    if isinstance(choices, list) and len(cast(list[object], choices)) == 1:
        (only,) = cast(list[object], choices)
        if isinstance(only, str):
            return only
    raise DataFormatError(
        f"{model.__name__} must declare a single literal resourceType for FHIR import"
    )


def _resources(model: type[BaseModel], document: Record) -> list[JsonValue]:
    expected = _model_resource_type(model)
    resource_type = document.get("resourceType")
    if resource_type == expected:
        return [document]
    if resource_type != "Bundle":
        raise DataFormatError(
            f"Expected a {expected} resource or a collection Bundle, got {resource_type!r}"
        )
    if document.get("type") != "collection":
        raise DataFormatError("Only collection Bundles are imported as record lists")
    entries = document.get("entry", [])
    resources: list[JsonValue] = []
    for index, entry in enumerate(entries if isinstance(entries, list) else [entries]):
        resource = entry.get("resource") if isinstance(entry, dict) else None
        if not isinstance(resource, dict):
            raise DataFormatError(f"Bundle entry {index} has no resource")
        if resource.get("resourceType") != expected:
            raise DataFormatError(f"Bundle entry {index} is not a {expected} resource")
        resources.append(resource)
    return resources


# Tabular formats


def _columns(model: type[BaseModel], payloads: list[Record]) -> list[str]:
    declared = [
        field.serialization_alias or field.alias or name
        for name, field in model.model_fields.items()
    ]
    extra = sorted({key for payload in payloads for key in payload} - set(declared))
    return declared + extra


def _cell_text(value: JsonValue) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":"))


def _dump_delimited(
    columns: list[str], payloads: list[Record], data_format: DataFormat
) -> bytes:
    separator = data_format.token(SyntaxRole.FIELD_SEPARATOR)
    terminator = data_format.token(SyntaxRole.RECORD_SEPARATOR)
    rows = [
        columns,
        *(
            [_cell_text(payload.get(column)) for column in columns]
            for payload in payloads
        ),
    ]
    if not data_format.supports(SyntaxRole.STRING_QUOTE):
        for row in rows:
            for cell in row:
                if separator in cell or "\n" in cell or "\r" in cell:
                    raise DataFormatError(
                        f"{data_format.identifier} cells cannot contain tabs or line breaks; use CSV"
                    )
        return "".join(separator.join(row) + terminator for row in rows).encode("utf-8")
    output = io.StringIO(newline="")
    writer = csv.writer(
        output,
        delimiter=separator,
        lineterminator=terminator,
        quotechar=data_format.token(SyntaxRole.STRING_QUOTE),
        doublequote=True,
        quoting=csv.QUOTE_MINIMAL,
    )
    writer.writerows(rows)
    return output.getvalue().encode("utf-8")


def _read_delimited(text: str, data_format: DataFormat) -> list[list[JsonValue]]:
    separator = data_format.token(SyntaxRole.FIELD_SEPARATOR)
    if not data_format.supports(SyntaxRole.STRING_QUOTE):
        lines = text.split("\n")
        if lines and lines[-1] == "":
            lines.pop()
        return [
            cast(list[JsonValue], line.removesuffix("\r").split(separator))
            for line in lines
        ]
    reader = csv.reader(
        io.StringIO(text, newline=""),
        delimiter=separator,
        quotechar=data_format.token(SyntaxRole.STRING_QUOTE),
        doublequote=True,
        strict=True,
    )
    try:
        return [cast(list[JsonValue], row) for row in reader]
    except csv.Error as exc:
        raise DataFormatError(f"Malformed {data_format.identifier}: {exc}") from exc


def _dump_xlsx(columns: list[str], payloads: list[Record]) -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    if sheet is None:
        raise DataFormatError("Workbook has no worksheet")
    sheet.title = _SHEET_NAME
    rows = [
        columns,
        *(
            [_excel_cell(payload.get(column)) for column in columns]
            for payload in payloads
        ),
    ]
    for row in rows:
        sheet.append(row)
    for worksheet_row in sheet.iter_rows():
        for cell in worksheet_row:
            if isinstance(cell.value, str):
                # openpyxl otherwise treats '=' as a formula and '#N/A' as an error cell.
                cell.data_type = "s"
    output = io.BytesIO()
    workbook.save(output)
    return output.getvalue()


def _excel_cell(value: JsonValue) -> bool | int | float | str | None:
    if isinstance(value, (list, dict)):
        value = _cell_text(value)
    if (
        isinstance(value, int)
        and not isinstance(value, bool)
        and abs(value) >= _EXCEL_EXACT_INTEGER
    ):
        # Excel numbers carry only 15 significant digits.
        return str(value)
    if isinstance(value, str) and len(value) > _EXCEL_CELL_LIMIT:
        raise DataFormatError(
            f"Excel cell text exceeds the {_EXCEL_CELL_LIMIT} character limit"
        )
    if isinstance(value, str) and "\r" in value:
        # Workbook XML normalises CR to LF and openpyxl does not decode _x000D_.
        raise DataFormatError(
            "XLSX cells cannot preserve carriage returns; use CSV or JSON"
        )
    return value


def _read_xlsx(content: bytes) -> list[list[JsonValue]]:
    try:
        workbook = load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    except (
        Exception
    ) as exc:  # openpyxl raises zip, XML and key errors for invalid workbooks.
        raise DataFormatError(f"Not a readable XLSX workbook: {exc}") from exc
    try:
        if _SHEET_NAME in workbook.sheetnames:
            sheet = workbook[_SHEET_NAME]
        elif len(workbook.sheetnames) == 1:
            sheet = workbook.worksheets[0]
        else:
            raise DataFormatError(
                f"Workbooks with several sheets need a {_SHEET_NAME!r} sheet"
            )
        rows: list[list[JsonValue]] = []
        for row in sheet.iter_rows(values_only=True):
            cells = [_json_compatible(cell) for cell in row]
            while cells and cells[-1] is None:
                cells.pop()
            if cells:
                rows.append(cells)
        return rows
    finally:
        workbook.close()


def _from_rows(model: type[BaseModel], rows: list[list[JsonValue]]) -> list[JsonValue]:
    if not rows:
        raise DataFormatError("Tabular content requires a header row")
    header, *body = rows
    if not all(isinstance(column, str) and column for column in header):
        raise DataFormatError("Header cells must be non-empty text")
    columns = cast(list[str], header)
    if len(set(columns)) != len(columns):
        raise DataFormatError("Header contains duplicate columns")
    coercer = SchemaCoercer(model)
    schemas = {
        column: coercer.property_schema(coercer.root, column) for column in columns
    }
    records: list[JsonValue] = []
    for number, row in enumerate(body, start=2):
        if len(row) > len(columns):
            raise DataFormatError(f"Row {number} has more cells than the header")
        record: Record = {}
        for column, cell in zip(
            columns, row + [None] * (len(columns) - len(row)), strict=True
        ):
            if cell is None or cell == "":
                empty = _empty_cell(coercer.types(schemas[column]))
                if empty is not _ABSENT:
                    record[column] = cast(JsonValue, empty)
                continue
            record[column] = coercer.coerce(cell, schemas[column], decode_nested=True)
        records.append(record)
    return records


_ABSENT = object()


def _empty_cell(accepted: set[str]) -> object:
    if "null" in accepted:
        return None
    if "string" in accepted:
        return ""
    return _ABSENT


__all__ = [
    "DEFAULT_MAX_BYTES",
    "DataFormatError",
    "RecordValidationError",
    "dump_record",
    "dump_records",
    "load_record",
    "load_records",
    "read_record",
    "read_records",
    "write_record",
    "write_records",
]
