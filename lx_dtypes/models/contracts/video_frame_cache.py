from __future__ import annotations

from collections.abc import Mapping
from typing import cast

from pydantic import ConfigDict

from lx_dtypes.models.contracts.json_types import JsonValue

from ._frame_cache import FrameCacheManifestFields, FrameCacheValidationFields

FrameCacheLogValue = str | int | float | bool | list[int] | list[str]
FrameCacheLogPayload = dict[str, FrameCacheLogValue]


class FrameCacheManifestLogPayload(FrameCacheManifestFields):
    model_config = ConfigDict(extra="forbid", strict=True)

    def as_log_payload(self) -> FrameCacheLogPayload:
        return cast(
            FrameCacheLogPayload,
            self.model_dump(mode="python", exclude_none=True),
        )


class FrameCacheValidationLogPayload(
    FrameCacheValidationFields, FrameCacheManifestLogPayload
):
    db_extracted_frame_count: int = 0


def parse_frame_cache_manifest_payload(
    payload: Mapping[str, JsonValue] | None,
) -> FrameCacheManifestLogPayload:
    return FrameCacheManifestLogPayload.model_validate(payload or {})


def parse_frame_cache_validation_payload(
    payload: Mapping[str, JsonValue] | None,
) -> FrameCacheValidationLogPayload:
    return FrameCacheValidationLogPayload.model_validate(payload or {})


__all__ = [
    "FrameCacheLogPayload",
    "FrameCacheLogValue",
    "FrameCacheManifestLogPayload",
    "FrameCacheValidationLogPayload",
    "parse_frame_cache_manifest_payload",
    "parse_frame_cache_validation_payload",
]
