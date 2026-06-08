from __future__ import annotations

from collections.abc import Mapping
from typing import TypedDict

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator


type HuggingFaceModelMetaCommandValue = bool | int | str | None


class HuggingFaceModelMetaCommandData(TypedDict, total=False):
    model_id: str
    model_name: str
    labelset_name: str
    meta_version: str
    labelset_version: int | None


class HuggingFaceModelMetaCommandPayload(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
        strict=True,
    )

    model_id: str = Field(min_length=1)
    model_name: str = Field(min_length=1)
    labelset_name: str = Field(min_length=1)
    meta_version: str = Field(min_length=1)
    labelset_version: int | None = Field(default=None, ge=1)

    @field_validator("labelset_version", mode="before")
    @classmethod
    def _empty_labelset_version_is_unset(
        cls,
        value: HuggingFaceModelMetaCommandValue,
    ) -> HuggingFaceModelMetaCommandValue:
        if value == "":
            return None
        return value


def huggingface_model_meta_command_data_from_mapping(
    payload: Mapping[str, HuggingFaceModelMetaCommandValue],
) -> HuggingFaceModelMetaCommandData:
    data: HuggingFaceModelMetaCommandData = {
        "model_id": str(payload["model_id"]),
        "model_name": str(payload["model_name"]),
        "labelset_name": str(payload["labelset_name"]),
        "meta_version": str(payload["meta_version"]),
    }
    labelset_version = payload.get("labelset_version")
    if isinstance(labelset_version, int) and not isinstance(labelset_version, bool):
        data["labelset_version"] = labelset_version
    return data


def validate_huggingface_model_meta_command_payload(
    value: Mapping[str, HuggingFaceModelMetaCommandValue],
) -> HuggingFaceModelMetaCommandPayload:
    try:
        return HuggingFaceModelMetaCommandPayload.model_validate(
            huggingface_model_meta_command_data_from_mapping(value)
        )
    except ValidationError as exc:
        raise ValueError(str(exc)) from exc


__all__ = [
    "HuggingFaceModelMetaCommandData",
    "HuggingFaceModelMetaCommandPayload",
    "HuggingFaceModelMetaCommandValue",
    "huggingface_model_meta_command_data_from_mapping",
    "validate_huggingface_model_meta_command_payload",
]
