"""Exact electrical/video clock conversion and frame-window evaluation."""

from __future__ import annotations

import math
from bisect import bisect_left
from fractions import Fraction
from typing import NamedTuple

from lx_dtypes.models.contracts.electrical_video_alignment import (
    ElectricalAlignmentError,
    ElectricalChannelStatistics,
    ElectricalFrameAggregationProfile,
    ElectricalFrameWindow,
    ElectricalFrameWindowStatus,
    ElectricalVideoAlignment,
)
from lx_dtypes.models.contracts.electrosurgical_measurements import (
    ElectrosurgicalMeasurementSeries,
)
from lx_dtypes.models.contracts.video_provenance import (
    RecordingSynchronization,
    VideoProvenanceBundle,
)

from .contracts import parse_contract


def _interpolate(
    points: list[tuple[int, int]], value: int | Fraction, *, label: str
) -> Fraction:
    """Piecewise-linear map through strictly increasing ``(x, y)`` anchor pairs."""
    xs = [x for x, _ in points]
    if not xs[0] <= value <= xs[-1]:
        raise ElectricalAlignmentError(
            f"{label} timestamp lies outside the measured synchronization interval"
        )
    right = min(max(1, bisect_left(xs, value)), len(points) - 1)
    (x0, y0), (x1, y1) = points[right - 1], points[right]
    return y0 + Fraction(y1 - y0, x1 - x0) * (value - x0)


def recording_to_electrical_ticks(
    synchronization: RecordingSynchronization, recording_timestamp: int | Fraction
) -> Fraction:
    """Convert recording-video PTS ticks to exact electrical-clock ticks."""
    points = [
        (a.video_timestamp, a.electrical_timestamp) for a in synchronization.anchors
    ]
    return _interpolate(points, recording_timestamp, label="Recording")


def electrical_to_recording_ticks(
    synchronization: RecordingSynchronization, electrical_timestamp: int | Fraction
) -> Fraction:
    """Convert electrical-clock ticks to exact recording-video PTS ticks."""
    points = [
        (a.electrical_timestamp, a.video_timestamp) for a in synchronization.anchors
    ]
    return _interpolate(points, electrical_timestamp, label="Electrical")


def _recording_frame_indices(proof: VideoProvenanceBundle) -> list[int]:
    """Compose verified ancestry from the published output back to the recording."""
    indices = list(range(len(proof.transformations[-1].output.presentation_timestamps)))
    for edge in reversed(proof.transformations):
        indices = [edge.source_frame_indices[index] for index in indices]
    return indices


def _window_ends(
    recording_indices: list[int],
    recording_ticks: list[int],
    recording_end_timestamp: int | None,
) -> list[int | None]:
    ends: list[int | None] = [None] * len(recording_indices)
    following: int | None = recording_end_timestamp
    for position in range(len(recording_indices) - 1, -1, -1):
        ends[position] = following
        if (
            position == 0
            or recording_indices[position - 1] != recording_indices[position]
        ):
            following = recording_ticks[recording_indices[position]]
    return ends


def _validate_inputs(
    proof: VideoProvenanceBundle,
    series: ElectrosurgicalMeasurementSeries,
    profile: ElectricalFrameAggregationProfile,
) -> RecordingSynchronization:
    sync = proof.synchronization
    if sync is None:
        raise ElectricalAlignmentError(
            "Independent clocks require recording synchronization anchors"
        )
    timestamps = series.timestamps
    if sync.session_id != timestamps.session_id or (
        sync.electrical_clock_id != timestamps.clock_id
    ):
        raise ElectricalAlignmentError(
            "Electrical data belongs to a different session or clock"
        )
    if Fraction(timestamps.time_base_num, timestamps.time_base_den) != Fraction(
        sync.electrical_time_base_num, sync.electrical_time_base_den
    ):
        raise ElectricalAlignmentError(
            "Electrical timestamp units differ from the synchronized device clock"
        )
    uncertainty = Fraction(sync.uncertainty_num, sync.uncertainty_den)
    if uncertainty > profile.max_alignment_uncertainty_seconds:
        raise ElectricalAlignmentError(
            "Synchronization uncertainty exceeds the profile tolerance"
        )
    return sync


class _FrameIdentity(NamedTuple):
    """Where one output frame sits on the generation and recording timelines."""

    output_frame_index: int
    presentation_timestamp: int
    recording_frame_index: int
    recording_start_timestamp: int
    recording_end_timestamp: int | None


def _frame_window(
    frame: _FrameIdentity,
    status: ElectricalFrameWindowStatus,
    sample_range: tuple[int, int] | None = None,
    channels: list[ElectricalChannelStatistics] | None = None,
) -> ElectricalFrameWindow:
    return ElectricalFrameWindow(
        **frame._asdict(),
        status=status,
        sample_start_index=None if sample_range is None else sample_range[0],
        sample_end_index=None if sample_range is None else sample_range[1],
        channels=channels or [],
    )


def align_electrosurgical_measurements(
    proof: VideoProvenanceBundle,
    series: ElectrosurgicalMeasurementSeries,
    profile: ElectricalFrameAggregationProfile,
    *,
    recording_end_timestamp: int | None = None,
    first_output_frame: int = 0,
    output_frame_count: int | None = None,
) -> ElectricalVideoAlignment:
    """Derive frame-level electrical parameters on the published generation.

    ``recording_end_timestamp`` is the exclusive end of the original recording
    in its PTS time base (container origin plus duration). Without it the last
    window is reported as ``unbounded_interval``. ``first_output_frame`` and
    ``output_frame_count`` select a bounded consecutive frame range.
    """
    proof = parse_contract(VideoProvenanceBundle, proof)
    series = parse_contract(ElectrosurgicalMeasurementSeries, series)
    profile = parse_contract(ElectricalFrameAggregationProfile, profile)
    sync = _validate_inputs(proof, series, profile)
    recording = proof.transformations[0].source
    output = proof.transformations[-1].output
    recording_ticks = recording.presentation_timestamps
    if recording_end_timestamp is not None and (
        recording_end_timestamp <= recording_ticks[-1]
    ):
        raise ElectricalAlignmentError(
            "Recording end must follow the last recording presentation timestamp"
        )
    total = len(output.presentation_timestamps)
    count = (
        total - first_output_frame if output_frame_count is None else output_frame_count
    )
    if first_output_frame < 0 or count < 1 or first_output_frame + count > total:
        raise ElectricalAlignmentError("Requested frame range lies outside the video")

    recording_indices = _recording_frame_indices(proof)
    window_ends = _window_ends(
        recording_indices, recording_ticks, recording_end_timestamp
    )
    electrical_ticks = series.timestamps.presentation_timestamps
    electrical_base = Fraction(
        series.timestamps.time_base_num, series.timestamps.time_base_den
    )
    max_gap_ticks = profile.max_sample_gap_seconds / electrical_base
    first_anchor = sync.anchors[0].video_timestamp
    last_anchor = sync.anchors[-1].video_timestamp

    frames: list[ElectricalFrameWindow] = []
    for position in range(first_output_frame, first_output_frame + count):
        recording_index = recording_indices[position]
        start = recording_ticks[recording_index]
        end = window_ends[position]

        frame = _FrameIdentity(
            output_frame_index=position,
            presentation_timestamp=output.presentation_timestamps[position],
            recording_frame_index=recording_index,
            recording_start_timestamp=start,
            recording_end_timestamp=end,
        )

        if end is None:
            frames.append(_frame_window(frame, "unbounded_interval"))
            continue
        if start < first_anchor or end > last_anchor:
            frames.append(_frame_window(frame, "outside_synchronization"))
            continue
        window_start = recording_to_electrical_ticks(sync, start)
        window_end = recording_to_electrical_ticks(sync, end)
        if window_start < electrical_ticks[0] or window_end > electrical_ticks[-1]:
            frames.append(_frame_window(frame, "outside_electrical_recording"))
            continue
        low = bisect_left(electrical_ticks, window_start)
        high = bisect_left(electrical_ticks, window_end)
        # Check every interval touching the window, including the ones that
        # straddle its bounds; ``high`` is a valid index because end <= last tick.
        gap = any(
            electrical_ticks[index + 1] - electrical_ticks[index] > max_gap_ticks
            for index in range(max(low - 1, 0), high)
        )
        status: ElectricalFrameWindowStatus = (
            "sample_gap"
            if gap
            else "insufficient_samples"
            if high - low < profile.min_samples_per_frame
            else "complete"
        )
        statistics = (
            [
                ElectricalChannelStatistics(
                    channel_id=channel.channel_id,
                    quantity=channel.quantity,
                    unit=channel.unit,
                    mean=math.fsum(channel.values[low:high]) / (high - low),
                    minimum=min(channel.values[low:high]),
                    maximum=max(channel.values[low:high]),
                )
                for channel in series.channels
            ]
            if status == "complete"
            else []
        )
        frames.append(_frame_window(frame, status, (low, high), statistics))

    return ElectricalVideoAlignment(
        profile=profile,
        generation_content_hash=output.content_hash,
        generation_time_base_num=output.time_base_num,
        generation_time_base_den=output.time_base_den,
        recording_content_hash=recording.content_hash,
        recording_time_base_num=recording.time_base_num,
        recording_time_base_den=recording.time_base_den,
        session_id=sync.session_id,
        electrical_clock_id=sync.electrical_clock_id,
        electrical_time_base_num=sync.electrical_time_base_num,
        electrical_time_base_den=sync.electrical_time_base_den,
        synchronization_method=sync.method,
        alignment_uncertainty_num=sync.uncertainty_num,
        alignment_uncertainty_den=sync.uncertainty_den,
        measurement_source_sha256=series.source_sha256,
        status="complete"
        if all(frame.status == "complete" for frame in frames)
        else "incomplete",
        frames=frames,
    )


__all__ = [
    "align_electrosurgical_measurements",
    "electrical_to_recording_ticks",
    "recording_to_electrical_ticks",
]
