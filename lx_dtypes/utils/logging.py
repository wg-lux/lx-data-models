from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Callable, Iterable, Literal, Tuple

import yaml

from lx_dtypes.models.base_models.log import Log, LogLevel, LogScope

# Default location inside the repository package
_DEFAULT_LOG_ROOT = Path(__file__).resolve().parent.parent / "data" / "logs"


class ScopedLogWriter:
    """Write Log entries to scope-specific files with optional per-test scoping."""

    def __init__(
        self,
        scope: LogScope,
        *,
        root_dir: Path | None = None,
        filename_factory: Callable[[Log], str] | None = None,
        context_path_keys: Iterable[str] | None = None,
        output_format: Literal["jsonl", "yaml"] = "jsonl",
    ) -> None:
        self.scope = scope
        self._root_dir = (root_dir or _DEFAULT_LOG_ROOT).expanduser().resolve()
        self._scope_dir = self._root_dir / scope.value
        self._scope_dir.mkdir(parents=True, exist_ok=True)
        self._filename_factory = filename_factory
        keys = (
            tuple(context_path_keys)
            if context_path_keys is not None
            else ("test", "origin", "source")
        )
        self._context_path_keys: Tuple[str, ...] = keys
        self._output_format = output_format
        self._file_extension = "log.jsonl" if output_format == "jsonl" else "log.yaml"

    def _sanitize_segment(self, value: str) -> str:
        cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip())
        return cleaned or "context"

    def _parse_nodeid(self, nodeid: str) -> tuple[str | None, str | None]:
        parts = nodeid.split("::")
        if len(parts) >= 3:
            return parts[-2], parts[-1]
        if len(parts) == 2:
            return None, parts[-1]
        return None, parts[-1]

    def _context_path_segment(self, context: dict[str, Any]) -> str | None:
        if not self._context_path_keys:
            return None
        for key in self._context_path_keys:
            raw = context.get(key)
            if raw:
                return self._sanitize_segment(str(raw))
        return None

    def _dir_and_test_name(self, entry: Log) -> tuple[list[str], str | None]:
        context = entry.context or {}
        nodeid = context.get("test")
        explicit_class = context.get("test_class")
        explicit_name = context.get("test_name")

        derived_class: str | None = None
        derived_name: str | None = None
        if nodeid:
            derived_class, derived_name = self._parse_nodeid(str(nodeid))

        class_segment = explicit_class or derived_class
        test_name = explicit_name or derived_name

        segments: list[str] = []
        if class_segment:
            segments.append(self._sanitize_segment(str(class_segment)))
        else:
            fallback = self._context_path_segment(context)
            if fallback:
                segments.append(fallback)

        return segments, test_name

    def _default_filename(self, entry: Log, test_name: str | None) -> str:
        date_part = entry.timestamp.date().isoformat()
        if test_name:
            name = self._sanitize_segment(str(test_name))
            return f"{date_part}_{name}.{self._file_extension}"
        return f"{date_part}.{self._file_extension}"

    def _serialize_entry(self, entry: Log) -> str:
        if self._output_format == "yaml":
            payload = entry.model_dump(mode="json")
            return yaml.safe_dump(payload, sort_keys=False).strip()
        return entry.model_dump_json()

    def _log_path(self, entry: Log) -> Path:
        dir_segments, test_name = self._dir_and_test_name(entry)
        target_dir = self._scope_dir
        for segment in dir_segments:
            target_dir /= segment
        target_dir.mkdir(parents=True, exist_ok=True)

        filename = (
            self._filename_factory(entry)
            if self._filename_factory
            else self._default_filename(entry, test_name)
        )
        return target_dir / filename

    def log(
        self,
        message: str,
        *,
        level: LogLevel = LogLevel.INFO,
        context: dict[str, Any] | None = None,
    ) -> Log:
        entry = Log(message=message, level=level, scope=self.scope, context=context)
        self._write_entry(entry)
        return entry

    def _write_entry(self, entry: Log) -> None:
        log_file = self._log_path(entry)
        serialized = self._serialize_entry(entry)
        needs_separator = (
            self._output_format == "yaml"
            and log_file.exists()
            and log_file.stat().st_size > 0
        )

        with log_file.open("a", encoding="utf-8") as fh:
            if needs_separator:
                fh.write("\n---\n")
            fh.write(serialized)
            fh.write("\n")


def get_logger(
    scope: LogScope,
    *,
    root_dir: Path | None = None,
    filename_factory: Callable[[Log], str] | None = None,
    context_path_keys: Iterable[str] | None = None,
    output_format: Literal["jsonl", "yaml"] = "jsonl",
) -> ScopedLogWriter:
    """Return a ScopedLogWriter for the provided scope."""

    return ScopedLogWriter(
        scope,
        root_dir=root_dir,
        filename_factory=filename_factory,
        context_path_keys=context_path_keys,
        output_format=output_format,
    )
