from __future__ import annotations

from collections.abc import Mapping
from typing import cast

from pydantic import ConfigDict, RootModel, field_validator

from .json_types import JsonNull, JsonValue


type VideoTextMetaValue = (
    JsonValue | JsonNull | list["VideoTextMetaValue"] | dict[str, "VideoTextMetaValue"]
)


class VideoTextMetaPayload(RootModel[dict[str, VideoTextMetaValue]]):
    model_config = ConfigDict(frozen=True, strict=True)

    @field_validator("root", mode="before")
    @classmethod
    def normalize_root(
        cls, value: Mapping[str, VideoTextMetaValue]
    ) -> dict[str, VideoTextMetaValue]:
        if not isinstance(value, Mapping):
            raise ValueError("video text metadata must be a JSON object")
        mapping = cast(Mapping[object, VideoTextMetaValue], value)
        return {
            str(key): cast(VideoTextMetaValue, item) for key, item in mapping.items()
        }

    def to_dict(self) -> dict[str, VideoTextMetaValue]:
        return cast(dict[str, VideoTextMetaValue], self.model_dump(mode="python"))


__all__ = ["VideoTextMetaPayload", "VideoTextMetaValue"]
