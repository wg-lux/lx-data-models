from __future__ import annotations

from types import NoneType
from typing import Literal, TypeAlias

from pydantic import BaseModel, ConfigDict, Field

JsonNull: TypeAlias = NoneType
LxAnonymizerPerformanceMediaType: TypeAlias = Literal["video", "report"]
LxAnonymizerPerformanceCsvCell: TypeAlias = str | int | float | bool | JsonNull
LxAnonymizerPerformanceCsvRow: TypeAlias = dict[str, LxAnonymizerPerformanceCsvCell]


class LxAnonymizerDurationStatsPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    count: int = Field(ge=0)
    min: float = Field(ge=0.0)
    mean: float = Field(ge=0.0)
    max: float = Field(ge=0.0)
    p95: float = Field(ge=0.0)


class LxAnonymizerPerformanceRunPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_path: str
    staged_path: str
    media_type: LxAnonymizerPerformanceMediaType
    iteration: int = Field(ge=1)
    source_size_bytes: int = Field(ge=0)
    source_sha256: str
    ok: bool
    total_seconds: float = Field(ge=0.0)
    import_seconds: float = Field(ge=0.0)
    staging_seconds: float = Field(ge=0.0)
    anonymizer_seconds: float | JsonNull
    process_cpu_seconds: float = Field(ge=0.0)
    max_rss_kib_delta: int
    object_model: str = ""
    object_pk: int | JsonNull = None
    content_hash: str = ""
    processed_hash: str = ""
    raw_file_name: str = ""
    processed_file_name: str = ""
    short_circuited: bool = False
    error_type: str = ""
    error: str = ""


class LxAnonymizerPerformanceSummaryPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total_runs: int = Field(ge=0)
    ok_runs: int = Field(ge=0)
    failed_runs: int = Field(ge=0)
    short_circuited_runs: int = Field(ge=0)
    total_seconds: float = Field(ge=0.0)
    import_seconds: LxAnonymizerDurationStatsPayload
    anonymizer_seconds: LxAnonymizerDurationStatsPayload
    end_to_end_seconds: LxAnonymizerDurationStatsPayload


class LxAnonymizerPerformancePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: LxAnonymizerPerformanceSummaryPayload
    runs: list[LxAnonymizerPerformanceRunPayload]


LX_ANONYMIZER_PERFORMANCE_CSV_FIELDNAMES: tuple[str, ...] = (
    "source_path",
    "staged_path",
    "media_type",
    "iteration",
    "source_size_bytes",
    "source_sha256",
    "ok",
    "total_seconds",
    "import_seconds",
    "staging_seconds",
    "anonymizer_seconds",
    "process_cpu_seconds",
    "max_rss_kib_delta",
    "object_model",
    "object_pk",
    "content_hash",
    "processed_hash",
    "raw_file_name",
    "processed_file_name",
    "short_circuited",
    "error_type",
    "error",
)


def dump_lx_anonymizer_performance_run_csv_row(
    run: LxAnonymizerPerformanceRunPayload,
) -> LxAnonymizerPerformanceCsvRow:
    return {
        "source_path": run.source_path,
        "staged_path": run.staged_path,
        "media_type": run.media_type,
        "iteration": run.iteration,
        "source_size_bytes": run.source_size_bytes,
        "source_sha256": run.source_sha256,
        "ok": run.ok,
        "total_seconds": run.total_seconds,
        "import_seconds": run.import_seconds,
        "staging_seconds": run.staging_seconds,
        "anonymizer_seconds": run.anonymizer_seconds,
        "process_cpu_seconds": run.process_cpu_seconds,
        "max_rss_kib_delta": run.max_rss_kib_delta,
        "object_model": run.object_model,
        "object_pk": run.object_pk,
        "content_hash": run.content_hash,
        "processed_hash": run.processed_hash,
        "raw_file_name": run.raw_file_name,
        "processed_file_name": run.processed_file_name,
        "short_circuited": run.short_circuited,
        "error_type": run.error_type,
        "error": run.error,
    }


__all__ = [
    "LX_ANONYMIZER_PERFORMANCE_CSV_FIELDNAMES",
    "LxAnonymizerDurationStatsPayload",
    "LxAnonymizerPerformanceCsvCell",
    "LxAnonymizerPerformanceCsvRow",
    "LxAnonymizerPerformanceMediaType",
    "LxAnonymizerPerformancePayload",
    "LxAnonymizerPerformanceRunPayload",
    "LxAnonymizerPerformanceSummaryPayload",
    "dump_lx_anonymizer_performance_run_csv_row",
]
