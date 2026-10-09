"""Exact frame lineage and explicit recording-clock synchronization for exchange."""

from __future__ import annotations

from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

FrameIndex = Annotated[int, Field(ge=0)]
OpaqueClockId = Annotated[str, Field(pattern=r"^[0-9a-f]{32}$")]


class VideoFrameTimeline(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    time_base_num: int = Field(gt=0)
    time_base_den: int = Field(gt=0)
    presentation_timestamps: list[int] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_timestamps(self) -> Self:
        ticks = self.presentation_timestamps
        if ticks[0] < 0 or any(b <= a for a, b in zip(ticks, ticks[1:])):
            raise ValueError(
                "Presentation timestamps must be nonnegative and strictly increasing"
            )
        return self


class VideoFrameProvenancePayload(BaseModel):
    """List position is the output presentation-frame index, never packet order."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    schema_version: Literal["1"] = "1"
    method: Literal["ffmpeg_encoder_input_v1", "opencv_decoder_input_v1"] = (
        "ffmpeg_encoder_input_v1"
    )
    decoder_timestamp_offset_num: int = 0
    decoder_timestamp_offset_den: int = Field(default=1, gt=0)
    encoder_timestamp_offset_num: int = 0
    encoder_timestamp_offset_den: int = Field(default=1, gt=0)
    source: VideoFrameTimeline
    output: VideoFrameTimeline
    source_frame_indices: list[FrameIndex] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_indices(self) -> Self:
        indices = self.source_frame_indices
        if len(indices) != len(self.output.presentation_timestamps):
            raise ValueError("Every output frame requires exactly one source index")
        if any(index >= len(self.source.presentation_timestamps) for index in indices):
            raise ValueError("Source frame index exceeds decoded source timeline")
        if any(b < a for a, b in zip(indices, indices[1:])):
            raise ValueError("Source frame order must not reverse")
        if self.source.content_hash == self.output.content_hash and (
            self.source != self.output or indices != list(range(len(indices)))
        ):
            raise ValueError("Identical content requires identical frame lineage")
        return self


class SynchronizationAnchor(BaseModel):
    """One event observed on both recording clocks, captured during acquisition."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    video_timestamp: int = Field(ge=0)
    electrical_timestamp: int


class ElectricalTimestampSeries(BaseModel):
    """Native ticks for one independent device's uninterrupted recording epoch."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    session_id: OpaqueClockId
    clock_id: OpaqueClockId
    time_base_num: int = Field(gt=0)
    time_base_den: int = Field(gt=0)
    presentation_timestamps: list[int] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_order(self) -> Self:
        ticks = self.presentation_timestamps
        if any(b <= a for a, b in zip(ticks, ticks[1:])):
            raise ValueError("Electrical timestamps must increase within one clock epoch")
        return self


class RecordingSynchronization(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    session_id: OpaqueClockId
    video_clock_id: OpaqueClockId
    electrical_clock_id: OpaqueClockId
    source_content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    electrical_time_base_num: int = Field(gt=0)
    electrical_time_base_den: int = Field(gt=0)
    method: Literal["shared_hardware_event", "measured_clock_correlation"]
    anchors: list[SynchronizationAnchor] = Field(min_length=2)
    # Conservative acquisition-supplied bound, including anchor measurement and
    # drift between anchors. The receiver does not manufacture this bound.
    uncertainty_num: int = Field(ge=0)
    uncertainty_den: int = Field(gt=0)

    @model_validator(mode="after")
    def validate_clocks(self) -> Self:
        if self.video_clock_id == self.electrical_clock_id:
            raise ValueError("Independent devices require distinct clock identities")
        if any(
            b.video_timestamp <= a.video_timestamp
            or b.electrical_timestamp <= a.electrical_timestamp
            for a, b in zip(self.anchors, self.anchors[1:])
        ):
            raise ValueError("Synchronization anchors must increase on both clocks")
        return self


class VideoProvenanceBundle(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    schema_version: Literal["1"] = "1"
    transformations: list[VideoFrameProvenancePayload] = Field(
        min_length=1, max_length=128
    )
    synchronization: RecordingSynchronization | None = None

    @model_validator(mode="after")
    def validate_chain(self) -> Self:
        seen = {self.transformations[0].source.content_hash}
        for index, entry in enumerate(self.transformations):
            if index and self.transformations[index - 1].output != entry.source:
                raise ValueError("Frame provenance chain is disconnected")
            if entry.output.content_hash in seen:
                raise ValueError("Frame provenance chain contains a cycle")
            seen.add(entry.output.content_hash)
        if self.synchronization is not None and (
            self.synchronization.source_content_hash
            != self.transformations[0].source.content_hash
        ):
            raise ValueError("Synchronization belongs to a different recording")
        return self
