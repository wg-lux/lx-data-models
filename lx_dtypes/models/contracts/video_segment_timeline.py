"""Exact segment coordinates on a processed generation and its original recording.

A segment's first and last *included* frame are expressed as integer
presentation timestamp ticks in the stream's rational time base. Original
recording coordinates are present only when decoder ancestry is verified; they
are composed from ``VideoFrameProvenancePayload.source_frame_indices`` and are
never inferred from timestamp proximity.
"""

from __future__ import annotations

from typing import Literal, NotRequired, Self, TypedDict

from pydantic import BaseModel, ConfigDict, Field, model_validator

RecordingMappingStatus = Literal["verified", "unresolved"]


class VideoSegmentGenerationCoordinatesData(TypedDict):
    content_hash: str
    time_base_num: int
    time_base_den: int
    first_frame_number: int
    last_frame_number: int
    first_presentation_timestamp: int
    last_presentation_timestamp: int


class VideoSegmentRecordingCoordinatesData(TypedDict):
    recording_content_hash: str
    time_base_num: int
    time_base_den: int
    first_frame_index: int
    last_frame_index: int
    first_presentation_timestamp: int
    last_presentation_timestamp: int


class VideoSegmentTimelineCoordinatesData(TypedDict):
    schema_version: Literal["1"]
    generation: VideoSegmentGenerationCoordinatesData
    recording_mapping_status: RecordingMappingStatus
    recording: NotRequired[VideoSegmentRecordingCoordinatesData | None]


class VideoSegmentGenerationCoordinates(BaseModel):
    """First and last included frame on the published processed generation."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    time_base_num: int = Field(gt=0)
    time_base_den: int = Field(gt=0)
    first_frame_number: int = Field(ge=0)
    last_frame_number: int = Field(ge=0)
    first_presentation_timestamp: int = Field(ge=0)
    last_presentation_timestamp: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_order(self) -> Self:
        if self.last_frame_number < self.first_frame_number:
            raise ValueError("Segment last frame must not precede its first frame")
        if (self.last_frame_number == self.first_frame_number) != (
            self.last_presentation_timestamp == self.first_presentation_timestamp
        ) or self.last_presentation_timestamp < self.first_presentation_timestamp:
            raise ValueError(
                "Generation timestamps must strictly increase with frame number"
            )
        return self


class VideoSegmentRecordingCoordinates(BaseModel):
    """Original-recording frames that produced the first and last included frame."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    recording_content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    time_base_num: int = Field(gt=0)
    time_base_den: int = Field(gt=0)
    first_frame_index: int = Field(ge=0)
    last_frame_index: int = Field(ge=0)
    first_presentation_timestamp: int = Field(ge=0)
    last_presentation_timestamp: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_order(self) -> Self:
        # Repetition can map several output frames to one recording frame.
        if self.last_frame_index < self.first_frame_index:
            raise ValueError("Recording frame order must not reverse within a segment")
        if (self.last_frame_index == self.first_frame_index) != (
            self.last_presentation_timestamp == self.first_presentation_timestamp
        ) or self.last_presentation_timestamp < self.first_presentation_timestamp:
            raise ValueError(
                "Recording timestamps must strictly increase with frame index"
            )
        return self


class VideoSegmentTimelineCoordinates(BaseModel):
    """Segment boundaries bound to exact generation and recording identities."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    schema_version: Literal["1"] = "1"
    generation: VideoSegmentGenerationCoordinates
    recording_mapping_status: RecordingMappingStatus
    recording: VideoSegmentRecordingCoordinates | None = None

    @model_validator(mode="after")
    def validate_recording_mapping(self) -> Self:
        verified = self.recording_mapping_status == "verified"
        if verified != (self.recording is not None):
            raise ValueError(
                "Recording coordinates are required exactly for verified ancestry"
            )
        return self


__all__ = [
    "RecordingMappingStatus",
    "VideoSegmentGenerationCoordinates",
    "VideoSegmentGenerationCoordinatesData",
    "VideoSegmentRecordingCoordinates",
    "VideoSegmentRecordingCoordinatesData",
    "VideoSegmentTimelineCoordinates",
    "VideoSegmentTimelineCoordinatesData",
]
