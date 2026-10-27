"""Read-only CSV projection of explicitly selected Django querysets.

Host code owns authorization, patient selection, transactions and database aliases.
No EndoReg imports or implicit database/model discovery are required.
"""

from __future__ import annotations

import base64
from collections.abc import Iterable, Iterator, Mapping
from pathlib import Path
from typing import Any, Literal

from django.db.models import Field, Model, QuerySet

from lx_dtypes.stats.standardized import CsvTable, records_table, write_csv_tables

BinaryPolicy = Literal["reject", "base64"]


def queryset_tables(
    querysets: Mapping[str, QuerySet[Model]],
    *,
    binary: BinaryPolicy = "reject",
) -> dict[str, CsvTable]:
    """Retain concrete columns and explicit through rows for every forward M:N field.

    Relations are restricted to the selected source IDs on the queryset's own
    database, including custom through-model fields. Foreign keys use their stored
    attnames (e.g. patient_id); file fields export their stored name and files are
    never opened. Rows are ordered by primary key unless the queryset is ordered.

    Binary columns (for example encryption keys or prediction arrays) are rejected
    unless ``binary="base64"`` explicitly opts in to exporting them as base64 text.
    Querysets whose joins repeat a record are rejected; apply ``.distinct()``.
    """
    tables: dict[str, CsvTable] = {}
    for name, queryset in querysets.items():
        if name in tables:
            raise ValueError(f"Duplicate export table: {name}")
        if queryset.query.is_sliced:
            raise ValueError("Use an explicit ID filter instead of a sliced queryset")
        model = queryset.model
        fields = model._meta.concrete_fields
        columns = [field.attname for field in fields]
        binary_columns = _binary_columns(model, fields, binary)
        if not queryset.ordered:
            queryset = queryset.order_by("pk")
        pk_column = model._meta.pk.attname
        rows = _unique_rows(
            _encode_binary(
                queryset.values(*columns).iterator(chunk_size=2000), binary_columns
            ),
            pk_column,
            name,
        )
        tables[name] = records_table(columns, rows)
        for field in model._meta.many_to_many:
            through = field.remote_field.through
            if through is None:
                raise ValueError(f"Unresolved through model for {field.name}")
            relation_name = f"{name}__{field.name}"
            if relation_name in tables or relation_name in querysets:
                raise ValueError(f"Duplicate export table: {relation_name}")
            source_field = field.m2m_field_name()
            through_fields = through._meta.concrete_fields
            relation_columns = [item.attname for item in through_fields]
            relation_binary = _binary_columns(through, through_fields, binary)
            relations = (
                through._default_manager.using(queryset.db)
                .filter(
                    **{f"{source_field}__in": queryset.values_list("pk", flat=True)}
                )
                .order_by("pk")
            )
            tables[relation_name] = records_table(
                relation_columns,
                _encode_binary(
                    relations.values(*relation_columns).iterator(chunk_size=2000),
                    relation_binary,
                ),
            )
    return tables


def export_querysets(
    querysets: Mapping[str, QuerySet[Model]],
    directory: Path,
    *,
    overwrite: bool = False,
    binary: BinaryPolicy = "reject",
    files: Mapping[str, Path] | None = None,
) -> Path:
    """Export selected EndoReg (or other Django) records using current ORM fields.

    ``files`` bundles host-resolved files such as frame images next to the CSVs.
    """
    return write_csv_tables(
        queryset_tables(querysets, binary=binary),
        directory,
        source="django_querysets",
        overwrite=overwrite,
        files=files,
    )


def _binary_columns(
    model: type[Model], fields: Iterable[Field[Any, Any]], policy: BinaryPolicy
) -> list[str]:
    columns = [
        field.attname for field in fields if field.get_internal_type() == "BinaryField"
    ]
    if columns and policy == "reject":
        raise ValueError(
            f"{model._meta.label} has binary columns {columns}; exclude the model "
            'or pass binary="base64" explicitly'
        )
    return columns


def _encode_binary(
    rows: Iterator[dict[str, object]], columns: list[str]
) -> Iterator[dict[str, object]]:
    for row in rows:
        for column in columns:
            value = row[column]
            if value is not None:
                row[column] = base64.b64encode(bytes(value)).decode("ascii")  # type: ignore[arg-type]
        yield row


def _unique_rows(
    rows: Iterator[dict[str, object]], pk_column: str, table: str
) -> Iterator[dict[str, object]]:
    seen: set[object] = set()
    for row in rows:
        key = row[pk_column]
        if key in seen:
            raise ValueError(
                f"{table} repeats primary key {key!r}; apply .distinct() to "
                "querysets filtered across relations"
            )
        seen.add(key)
        yield row
