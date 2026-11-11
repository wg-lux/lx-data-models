"""Deterministic alignment of electrical samples to video frames through PTS.

Presentation timestamps (PTS) are the integer display times of video frames in
a rational time base. They are authoritative for frame identity and for this
alignment; nominal frames per second are never used.

The alignment is exact rational arithmetic in three steps:

1. Verified frame ancestry (``VideoProvenanceBundle``) maps each output frame of
   the published generation to the original recording frame that produced it.
2. Each output frame receives a half-open window on the recording timeline: from
   its recording frame's PTS to the PTS of the next *distinct* recording frame
   used by a later output frame. Consecutive output frames that repeat one
   recording frame share its window; frames dropped by decimation extend the
   preceding window, so windows of distinct frames never overlap.
3. Synchronization anchors captured during acquisition convert window bounds to
   the electrical clock by piecewise-linear interpolation between neighbouring
   anchors. Extrapolation beyond the first or last anchor is rejected.

Samples with ``window_start <= t < window_end`` belong to a frame. Gaps, missing
coverage, and unbounded terminal windows produce an explicit status and no
values. Nothing is interpolated, zero-filled or carried forward.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Final, Literal, Self

from pydantic import Field, model_validator

from lx_dtypes.models.model import FrozenContractModel

from .electrosurgical_measurements import (
    ElectrosurgicalMeasurementSeries,
    ElectrosurgicalQuantity,
    ElectrosurgicalUnit,
)
from .video_provenance import RecordingSynchronization, VideoProvenanceBundle

ELECTRICAL_FRAME_WINDOW_ALGORITHM: Final = "electrical_frame_window_v1"

ElectricalFrameWindowStatus = Literal[
    "complete",
    "outside_synchronization",
    "outside_electrical_recording",
    "sample_gap",
    "insufficient_samples",
    "unbounded_interval",
]
_NO_SAMPLE_RANGE_STATUSES: Final[frozenset[ElectricalFrameWindowStatus]] = frozenset(
    {"outside_synchronization", "outside_electrical_recording", "unbounded_interval"}
)
_SHA256 = r"^[0-9a-f]{64}$"
_OPAQUE_ID = r"^[0-9a-f]{32}$"


class ElectricalAlignmentError(ValueError):
    """The inputs cannot be aligned without violating a timeline invariant."""


class ElectricalFrameAggregationProfile(FrozenContractModel):
    """Versioned tolerances for frame-level electrical parameters, in seconds."""

    profile_id: str = Field(pattern=r"^[a-z][a-z0-9_.-]{0,63}$")
    profile_version: int = Field(ge=1)
    max_sample_gap_num: int = Field(gt=0)
    max_sample_gap_den: int = Field(gt=0)
    max_alignment_uncertainty_num: int = Field(ge=0)
    max_alignment_uncertainty_den: int = Field(gt=0)
    min_samples_per_frame: int = Field(default=1, ge=1)

    @property
    def max_sample_gap_seconds(self) -> Fraction:
        return Fraction(self.max_sample_gap_num, self.max_sample_gap_den)

    @property
    def max_alignment_uncertainty_seconds(self) -> Fraction:
        return Fraction(
            self.max_alignment_uncertainty_num, self.max_alignment_uncertainty_den
        )


class ElectricalChannelStatistics(FrozenContractModel):
    """Unweighted sample statistics of one channel within one frame window."""

    channel_id: str = Field(min_length=1)
    quantity: ElectrosurgicalQuantity
    unit: ElectrosurgicalUnit
    mean: float = Field(allow_inf_nan=False)
    minimum: float = Field(allow_inf_nan=False)
    maximum: float = Field(allow_inf_nan=False)

    @model_validator(mode="after")
    def validate_range(self) -> Self:
        if self.maximum < self.minimum:
            raise ValueError("Channel maximum must not be below its minimum")
        return self


class ElectricalFrameWindow(FrozenContractModel):
    """One output frame, its recording-timeline window and its parameters.

    ``presentation_timestamp`` is on the published generation; the recording
    bounds are on the original recording. ``recording_end_timestamp`` and
    ``sample_end_index`` are exclusive.
    """

    output_frame_index: int = Field(ge=0)
    presentation_timestamp: int = Field(ge=0)
    recording_frame_index: int = Field(ge=0)
    recording_start_timestamp: int = Field(ge=0)
    recording_end_timestamp: int | None
    status: ElectricalFrameWindowStatus
    sample_start_index: int | None = Field(default=None, ge=0)
    sample_end_index: int | None = Field(default=None, ge=0)
    channels: list[ElectricalChannelStatistics] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_status(self) -> Self:
        if (self.recording_end_timestamp is None) != (
            self.status == "unbounded_interval"
        ):
            raise ValueError("Only an unbounded window may lack a recording end")
        if (
            self.recording_end_timestamp is not None
            and self.recording_end_timestamp <= self.recording_start_timestamp
        ):
            raise ValueError("Recording window end must follow its start")
        has_range = self.sample_start_index is not None
        if has_range != (self.sample_end_index is not None):
            raise ValueError("Sample range requires both start and end")
        if has_range == (self.status in _NO_SAMPLE_RANGE_STATUSES):
            raise ValueError(f"Sample range presence disagrees with {self.status}")
        if (
            self.sample_start_index is not None
            and self.sample_end_index is not None
            and self.sample_end_index < self.sample_start_index
        ):
            raise ValueError("Sample range end must not precede its start")
        if bool(self.channels) != (self.status == "complete"):
            raise ValueError("Channel statistics are published only when complete")
        return self


class ElectricalVideoAlignment(FrozenContractModel):
    """Frame-level electrical parameters bound to every identity they depend on.

    A changed generation, recording, clock, measurement source, profile or
    algorithm produces a different binding; results are never reused across them.
    """

    schema_version: Literal["1"] = "1"
    algorithm: Literal["electrical_frame_window_v1"] = ELECTRICAL_FRAME_WINDOW_ALGORITHM
    profile: ElectricalFrameAggregationProfile
    generation_content_hash: str = Field(pattern=_SHA256)
    generation_time_base_num: int = Field(gt=0)
    generation_time_base_den: int = Field(gt=0)
    recording_content_hash: str = Field(pattern=_SHA256)
    recording_time_base_num: int = Field(gt=0)
    recording_time_base_den: int = Field(gt=0)
    session_id: str = Field(pattern=_OPAQUE_ID)
    electrical_clock_id: str = Field(pattern=_OPAQUE_ID)
    electrical_time_base_num: int = Field(gt=0)
    electrical_time_base_den: int = Field(gt=0)
    synchronization_method: Literal[
        "shared_hardware_event", "measured_clock_correlation"
    ]
    alignment_uncertainty_num: int = Field(ge=0)
    alignment_uncertainty_den: int = Field(gt=0)
    measurement_source_sha256: str = Field(pattern=_SHA256)
    status: Literal["complete", "incomplete"]
    frames: list[ElectricalFrameWindow] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_frames(self) -> Self:
        first = self.frames[0].output_frame_index
        if any(
            frame.output_frame_index != first + offset
            for offset, frame in enumerate(self.frames)
        ):
            raise ValueError("Aligned frames must be consecutive output frames")
        complete = all(frame.status == "complete" for frame in self.frames)
        if complete != (self.status == "complete"):
            raise ValueError("Alignment status must reflect every frame status")
        return self


def recording_to_electrical_ticks(
    synchronization: RecordingSynchronization, recording_timestamp: int | Fraction
) -> Fraction:
    "Convert recording-video PTS ticks to exact electrical-clock ticks."
    from lx_dtypes.evaluation.electrical import (
        recording_to_electrical_ticks as evaluate,
    )

    return evaluate(synchronization, recording_timestamp)


def electrical_to_recording_ticks(
    synchronization: RecordingSynchronization, electrical_timestamp: int | Fraction
) -> Fraction:
    "Convert electrical-clock ticks to exact recording-video PTS ticks."
    from lx_dtypes.evaluation.electrical import (
        electrical_to_recording_ticks as evaluate,
    )

    return evaluate(synchronization, electrical_timestamp)


def align_electrosurgical_measurements(
    proof: VideoProvenanceBundle,
    series: ElectrosurgicalMeasurementSeries,
    profile: ElectricalFrameAggregationProfile,
    *,
    recording_end_timestamp: int | None = None,
    first_output_frame: int = 0,
    output_frame_count: int | None = None,
) -> ElectricalVideoAlignment:
    "Derive frame-level electrical parameters on the published generation.\n\n``recording_end_timestamp`` is the exclusive end of the original recording\nin its PTS time base (container origin plus duration). Without it the last\nwindow is reported as ``unbounded_interval``. ``first_output_frame`` and\n``output_frame_count`` select a bounded consecutive frame range."
    from lx_dtypes.evaluation.electrical import (
        align_electrosurgical_measurements as evaluate,
    )

    return evaluate(
        proof,
        series,
        profile,
        recording_end_timestamp=recording_end_timestamp,
        first_output_frame=first_output_frame,
        output_frame_count=output_frame_count,
    )


__all__ = [
    "ELECTRICAL_FRAME_WINDOW_ALGORITHM",
    "ElectricalAlignmentError",
    "ElectricalChannelStatistics",
    "ElectricalFrameAggregationProfile",
    "ElectricalFrameWindow",
    "ElectricalFrameWindowStatus",
    "ElectricalVideoAlignment",
    "align_electrosurgical_measurements",
    "electrical_to_recording_ticks",
    "recording_to_electrical_ticks",
]
