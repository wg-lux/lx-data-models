from __future__ import annotations

from typing import cast

from pydantic import ConfigDict

from ._frame_cache import FrameCacheManifestFields, FrameCacheValidationFields

type JsonNull = None
type JsonScalar = str | int | float | bool
type JsonValue = JsonNull | JsonScalar | list[JsonValue] | dict[str, JsonValue]
type JsonObject = dict[str, JsonValue]
type JsonStringObject = dict[str, str]
type JsonNumericObject = dict[str, JsonScalar]


class VideoFrameCacheManifestLogPayload(FrameCacheManifestFields):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    def to_log_payload(self) -> dict[str, JsonValue]:
        return cast(
            dict[str, JsonValue],
            self.model_dump(mode="python", exclude_none=True),
        )


class VideoFrameCacheValidationLogPayload(
    FrameCacheValidationFields, VideoFrameCacheManifestLogPayload
):
    pass


__all__ = [
    "JsonNull",
    "JsonNumericObject",
    "JsonObject",
    "JsonScalar",
    "JsonStringObject",
    "JsonValue",
    "VideoFrameCacheManifestLogPayload",
    "VideoFrameCacheValidationLogPayload",
]
