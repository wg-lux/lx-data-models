"""Complete CSV projections of validated clinical records, with explicit source scope."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import re
import shutil
from collections.abc import Iterable, Mapping
from itertools import chain
from pathlib import Path, PurePosixPath
from tempfile import TemporaryDirectory
from typing import NotRequired, cast, get_args, get_origin, get_type_hints

import yaml
from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, model_validator
from pydantic_core import to_jsonable_python

from lx_dtypes.models.contracts.aidataset_export import AIDataSetFrameAnnotationExport
from lx_dtypes.models.contracts.json_types import JsonObject, JsonValue
from lx_dtypes.models.contracts.video_frame_annotations import (
    FrameBoxAnnotationBulkItemPayload,
)
from lx_dtypes.models.interface.DbInterface import DbInterface
from lx_dtypes.models.interface.KnowledgeBase import KnowledgeBaseRecordList
from lx_dtypes.models.interface.Ledger import Ledger, LedgerRecordList
from lx_dtypes.models.ledger.case import Case
from lx_dtypes.models.ledger.medical import (
    PatientMedicalLedger,
    PatientMedicationSchedule,
    l_medical_lookup,
    l_medical_models,
)
from lx_dtypes.models.ledger.p_examination.Pydantic import PExamination
from lx_dtypes.models.ledger.p_video_segment.Pydantic import SerializedPVideoSegment
from lx_dtypes.models.ledger.p_video_segment.state import PVideoSegmentState

_JSON_ROW = TypeAdapter(JsonObject)


class CsvTable(BaseModel):
    """A complete table; complex cells use JSON, null uses an empty CSV cell."""

    model_config = ConfigDict(extra="forbid", strict=True)
    columns: list[str] = Field(min_length=1)
    rows: list[JsonObject] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_columns(self) -> CsvTable:
        if len(set(self.columns)) != len(self.columns):
            raise ValueError("CSV columns must be unique")
        if any(set(row) - set(self.columns) for row in self.rows):
            raise ValueError("CSV row has undeclared columns")
        return self


def records_table(columns: Iterable[str], records: Iterable[object]) -> CsvTable:
    rows = [
        _JSON_ROW.validate_python(to_jsonable_python(row), strict=True)
        for row in records
    ]
    # Actual serialized fields are authoritative even when a DataDict annotation lags.
    names = list(dict.fromkeys([*columns, *(key for row in rows for key in row)]))
    return CsvTable(columns=names, rows=rows)


def model_table(model: type[BaseModel], records: Iterable[BaseModel]) -> CsvTable:
    validated = [
        model.model_validate(record.model_dump(mode="python")) for record in records
    ]
    return records_table(
        model.model_fields, (row.model_dump(mode="json") for row in validated)
    )


def _record_tables(records: object, contract: type) -> dict[str, CsvTable]:
    mapping = cast(Mapping[str, Iterable[object]], records)
    result: dict[str, CsvTable] = {}
    for name, annotation in get_type_hints(contract).items():
        if get_origin(annotation) is NotRequired:
            annotation = get_args(annotation)[0]
        row_type = get_args(annotation)[0]
        result[name] = records_table(row_type.__annotations__, mapping[name])
    if set(mapping) != set(result):
        raise ValueError("Record-list contract does not cover every exported table")
    return result


def ledger_tables(
    ledger: Ledger,
    *,
    medical_ledgers: Iterable[PatientMedicalLedger] = (),
    image_annotations: Iterable[AIDataSetFrameAnnotationExport] = (),
    box_annotations: Iterable[FrameBoxAnnotationBulkItemPayload] = (),
) -> dict[str, CsvTable]:
    """Include all ledger collections and explicitly supplied medical/media aggregates."""
    # A case may own examinations absent from the top-level examination map.
    by_uuid: dict[str, PExamination] = {}
    for examination in chain(
        ledger.patient_examinations.values(),
        (exam for case in ledger.cases.values() for exam in case.patient_examinations),
    ):
        identity = str(examination.uuid)
        if identity in by_uuid and by_uuid[identity] != examination:
            raise ValueError(f"Conflicting examination records for UUID {identity}")
        by_uuid[identity] = examination
    complete_ledger = ledger.model_copy(update={"patient_examinations": by_uuid})
    tables = _record_tables(complete_ledger.export_record_lists(), LedgerRecordList)
    tables["cases"] = model_table(
        Case.serialized_model_class(),
        (case.serialized_model for case in ledger.cases.values()),
    )
    # Serialized patient videos omit their segments; export them as their own tables.
    segments = [
        segment
        for video in ledger.patient_videos.values()
        for segment in video.patient_video_segments.values()
    ]
    tables["p_video_segments"] = model_table(
        SerializedPVideoSegment, (segment.serialized_model for segment in segments)
    )
    tables["p_video_segment_states"] = model_table(
        PVideoSegmentState, (segment.state for segment in segments)
    )
    medical_models = cast(dict[str, type[l_medical_models]], l_medical_lookup)
    medical: dict[str, dict[str, BaseModel]] = {name: {} for name in medical_models}

    def collect(record: l_medical_models) -> None:
        name = type(record).__name__
        serialized = record.serialized_model
        previous = medical[name].get(str(record.uuid))
        if previous is not None and previous != serialized:
            raise ValueError(f"Conflicting {name} records for UUID {record.uuid}")
        medical[name][str(record.uuid)] = serialized
        # Walk nested medical records, including medications only present in a plan
        # and lab values only present in a sample. Repeated identical UUIDs deduplicate.
        for field in type(record).model_fields:
            value = getattr(record, field)
            if isinstance(value, list):
                for child in value:
                    if isinstance(child, tuple(medical_models.values())):
                        collect(cast(l_medical_models, child))
        if isinstance(record, PatientMedicationSchedule):
            for block in record.medication_blocks:
                for row in block.rows:
                    if row.kind == "medication":
                        collect(row.medication)

    for aggregate in medical_ledgers:
        validated = PatientMedicalLedger.model_validate(
            aggregate.model_dump(mode="python")
        )
        collect(validated)
    for name, model in medical_models.items():
        table_name = re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower() + "s"
        tables[table_name] = model_table(
            model.serialized_model_class(), medical[name].values()
        )
    annotations = list(image_annotations)
    tables["image_annotations"] = model_table(
        AIDataSetFrameAnnotationExport, annotations
    )
    tables["frames"] = frames_table(annotations)
    tables["image_box_annotations"] = model_table(
        FrameBoxAnnotationBulkItemPayload, box_annotations
    )
    return tables


_FRAME_COLUMNS = (
    "frame_id",
    "frame_number",
    "timestamp",
    "relative_path",
    "file_path",
    "patient_video_file_uuid",
    "video_id",
    "video_uuid",
    "raw_video_hash",
    "original_file_name",
)
_SAFE_SEGMENT = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")


def frame_export_path(video_uuid: str, relative_path: str) -> str:
    """Return the export-relative image path of a frame: ``frames/<video>/<path>``."""
    parts = (video_uuid, *PurePosixPath(relative_path).parts)
    if not all(_SAFE_SEGMENT.fullmatch(part) for part in parts):
        raise ValueError(f"Unsafe frame path segment in {video_uuid}/{relative_path}")
    return "/".join(("frames", *parts))


def frames_table(annotations: Iterable[AIDataSetFrameAnnotationExport]) -> CsvTable:
    """One row per annotated frame, with the path its image takes in the export.

    Pass the images to `write_csv_tables(files=...)` under `export_path` so the
    annotation rows resolve to bundled files.
    """
    frames: dict[int, JsonObject] = {}
    for annotation in annotations:
        dumped = annotation.model_dump(mode="json")
        row: JsonObject = {column: dumped[column] for column in _FRAME_COLUMNS}
        row["export_path"] = frame_export_path(
            annotation.video_uuid, annotation.relative_path
        )
        previous = frames.get(annotation.frame_id)
        if previous is not None and previous != row:
            raise ValueError(
                f"Conflicting frame records for frame {annotation.frame_id}"
            )
        frames[annotation.frame_id] = row
    return records_table(
        (*_FRAME_COLUMNS, "export_path"),
        (frames[frame_id] for frame_id in sorted(frames)),
    )


def interface_tables(
    interface: DbInterface,
    *,
    medical_ledgers: Iterable[PatientMedicalLedger] = (),
    image_annotations: Iterable[AIDataSetFrameAnnotationExport] = (),
    box_annotations: Iterable[FrameBoxAnnotationBulkItemPayload] = (),
) -> dict[str, CsvTable]:
    """Export every KB record list plus examination, medical and image records."""
    return {
        **{
            f"knowledge_base/{name}": table
            for name, table in _record_tables(
                interface.knowledge_base.export_record_lists(), KnowledgeBaseRecordList
            ).items()
        },
        **{
            f"ledger/{name}": table
            for name, table in ledger_tables(
                interface.ledger,
                medical_ledgers=medical_ledgers,
                image_annotations=image_annotations,
                box_annotations=box_annotations,
            ).items()
        },
    }


def _json_cell_value(value: JsonValue) -> JsonValue:
    if isinstance(value, float):
        if math.isnan(value):
            raise ValueError("NaN cannot be exported")
        if math.isinf(value):
            return "Infinity" if value > 0 else "-Infinity"
    if isinstance(value, list):
        return [_json_cell_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _json_cell_value(item) for key, item in value.items()}
    return value


def _cell(value: JsonValue) -> str:
    value = _json_cell_value(value)
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":"))


def write_csv_tables(
    tables: Mapping[str, CsvTable],
    directory: Path,
    *,
    source: str,
    overwrite: bool = False,
    files: Mapping[str, Path] | None = None,
) -> Path:
    """Stage every CSV and bundled file before publishing; write the manifest last.

    ``files`` maps export-relative paths (e.g. from `frame_export_path`) to source
    files such as frame images; they are copied, never moved or linked.
    Existing unrelated files are retained. Publication uses atomic file replacement,
    not an atomic multi-file directory transaction; readers should use the manifest.
    """
    if not tables:
        raise ValueError("At least one export table is required")
    for name in tables:
        if not re.fullmatch(r"[a-z][a-z0-9_]*(/[a-z][a-z0-9_]*)?", name):
            raise ValueError(f"Invalid table path: {name}")
    bundled = dict(files or {})
    for relative, source_file in bundled.items():
        parts = PurePosixPath(relative).parts
        if (
            not parts
            or not all(_SAFE_SEGMENT.fullmatch(part) for part in parts)
            or relative != "/".join(parts)
            or relative.endswith(".csv")
            or relative == "export_manifest.yml"
        ):
            raise ValueError(f"Invalid bundled file path: {relative}")
        if not source_file.is_file():
            raise FileNotFoundError(f"Bundled source is not a file: {relative}")
    destinations = [directory / f"{name}.csv" for name in tables]
    destinations.extend(directory / relative for relative in sorted(bundled))
    destinations.append(directory / "export_manifest.yml")
    if not overwrite and any(path.exists() for path in destinations):
        raise FileExistsError("Export files exist; select overwrite explicitly")
    directory.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=".csv-export-", dir=directory) as temp:
        staging = Path(temp)
        manifest: JsonObject = {"schema_version": "1", "source": source, "tables": {}}
        entries: JsonObject = {}
        for name, table in sorted(tables.items()):
            table = CsvTable.model_validate(table.model_dump())
            path = staging / f"{name}.csv"
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("w", encoding="utf-8", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=table.columns)
                writer.writeheader()
                for row in table.rows:
                    writer.writerow({key: _cell(value) for key, value in row.items()})
            entries[f"{name}.csv"] = {
                "rows": len(table.rows),
                "columns": list(table.columns),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        manifest["tables"] = entries
        file_entries: JsonObject = {}
        for relative, source_file in sorted(bundled.items()):
            staged_file = staging / relative
            staged_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source_file, staged_file)
            file_entries[relative] = {
                "bytes": staged_file.stat().st_size,
                "sha256": hashlib.sha256(staged_file.read_bytes()).hexdigest(),
            }
        if file_entries:
            manifest["files"] = file_entries
        (staging / "export_manifest.yml").write_text(
            yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8"
        )
        for destination in destinations:
            destination.parent.mkdir(parents=True, exist_ok=True)
            staged = staging / destination.relative_to(directory)
            if overwrite:
                os.replace(staged, destination)
            else:
                os.link(staged, destination)
    return directory / "export_manifest.yml"
