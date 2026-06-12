from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass

from pydantic import BaseModel, ConfigDict, Field

from .json_types import JsonObject


@dataclass(frozen=True)
class TemporalInferenceDispatchResult:
    task_id: str
    mode: str
    status: str
    video_id: int
    model_meta_id: int
    queue: str
    history_id: int | None = None
    deleted_prediction_segments: int | None = None
    prediction_segments_count: int | None = None
    reason: str | None = None
    message: str | None = None
    blocked_by_history_id: int | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class TemporalInferenceHistoryResultPayload(BaseModel):
    model_config = ConfigDict(extra="ignore", strict=False)

    backend: str | None = None
    device: str | None = None
    duration_ms: float | None = None
    provenance: JsonObject = Field(default_factory=dict)
    score_frame_count: int | None = None
    score_label_count: int | None = None
    score_frame_numbers_present: bool | None = None
    score_timestamps_present: bool | None = None
    frame_source_mode: str | None = None
    requested_frame_source_mode: str | None = None
    resolved_frame_source_mode: str | None = None
    source_video_kind: str | None = None
    temporal_segment_count: int | None = None
    materialized_segment_count: int | None = None
    created_segment_count: int | None = None
    deleted_prediction_segments: int | None = None
    score_vectors_stored: bool | None = None


class TemporalInferenceHistoryConfigPayload(BaseModel):
    model_config = ConfigDict(extra="ignore", strict=False)

    kind: str | None = None
    model_meta_id: int | None = None
    replace_prediction_segments: bool = True
    delete_frames_after: bool = True
    ocr_frame_fraction: float | None = None
    ocr_cap: int = 10
    temporal_options: JsonObject = Field(default_factory=dict)
    raw_temporal_options: JsonObject = Field(default_factory=dict)
    queue: str = ""
    frame_source_mode: str | None = None
    requested_frame_source_mode: str | None = None
    resolved_frame_source_mode: str | None = None
    test_run: bool = False
    n_test_frames: int = 10
    deferred_reason: str | None = None
    blocked_by_history_id: int | None = None
    result: TemporalInferenceHistoryResultPayload | None = None


def parse_temporal_inference_history_config_payload(
    payload: Mapping[str, object] | None,
) -> TemporalInferenceHistoryConfigPayload:
    return TemporalInferenceHistoryConfigPayload.model_validate(payload or {})


def parse_temporal_inference_history_result_payload(
    payload: Mapping[str, object] | None,
) -> TemporalInferenceHistoryResultPayload:
    return TemporalInferenceHistoryResultPayload.model_validate(payload or {})


__all__ = [
    "TemporalInferenceDispatchResult",
    "TemporalInferenceHistoryConfigPayload",
    "TemporalInferenceHistoryResultPayload",
    "parse_temporal_inference_history_config_payload",
    "parse_temporal_inference_history_result_payload",
]
