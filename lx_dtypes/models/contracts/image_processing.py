from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field
from lx_dtypes.models.contracts.json_types import JsonValue


def _empty_combined_results() -> list[
    tuple[str, tuple[int, int, int, int], float, list[tuple[str, str]]]
]:
    return []


def _empty_modified_images() -> dict[tuple[str, str], str]:
    return {}


class ImageProcessingResultPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    filename: Path
    file_type: str
    extracted_text: str
    names_detected: list[str] = Field(default_factory=list)
    combined_results: list[
        tuple[
            str,
            tuple[int, int, int, int],
            float,
            list[tuple[str, str]],
        ]
    ] = Field(default_factory=_empty_combined_results)
    modified_images_map: dict[tuple[str, str], str] = Field(
        default_factory=_empty_modified_images
    )
    gender_pars: list[str] = Field(default_factory=list)
    llm_results: dict[str, JsonValue] = Field(default_factory=dict)


__all__ = ["ImageProcessingResultPayload"]
