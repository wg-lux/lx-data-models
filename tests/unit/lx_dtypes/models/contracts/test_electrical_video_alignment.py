from __future__ import annotations

from collections.abc import Callable
from fractions import Fraction

import pytest
from pydantic import ValidationError

from lx_dtypes.models.contracts.electrical_video_alignment import (
    ElectricalAlignmentError,
    ElectricalFrameAggregationProfile,
    ElectricalVideoAlignment,
    align_electrosurgical_measurements,
    electrical_to_recording_ticks,
    recording_to_electrical_ticks,
)
from lx_dtypes.models.contracts.electrosurgical_measurements import (
    ElectrosurgicalChannel,
    ElectrosurgicalMeasurementSeries,
)
from lx_dtypes.models.contracts.video_provenance import (
    ElectricalTimestampSeries,
    RecordingSynchronization,
    SynchronizationAnchor,
    VideoFrameProvenancePayload,
    VideoFrameTimeline,
    VideoProvenanceBundle,
)

SESSION = "1" * 32
VIDEO_CLOCK = "2" * 32
ELECTRICAL_CLOCK = "3" * 32
RECORDING_HASH = "a" * 64
# Recording PTS in milliseconds (25 fps); electrical ticks of 100 microseconds.
RECORDING_TICKS = [0, 40, 80, 120, 160]
# Electrical clock starts 500 ms ahead of the video clock: e = 5000 + 10 * v.
OFFSET_ANCHORS = [(0, 5000), (1000, 15000)]


def _timeline(content_hash: str, ticks: list[int]) -> VideoFrameTimeline:
    return VideoFrameTimeline(
        content_hash=content_hash,
        time_base_num=1,
        time_base_den=1000,
        presentation_timestamps=ticks,
    )


def _sync(
    anchors: list[tuple[int, int]] = OFFSET_ANCHORS,
    *,
    uncertainty: Fraction = Fraction(1, 10000),
    clock: str = ELECTRICAL_CLOCK,
    time_base_den: int = 10000,
) -> RecordingSynchronization:
    return RecordingSynchronization(
        session_id=SESSION,
        video_clock_id=VIDEO_CLOCK,
        electrical_clock_id=clock,
        source_content_hash=RECORDING_HASH,
        electrical_time_base_num=1,
        electrical_time_base_den=time_base_den,
        method="shared_hardware_event",
        anchors=[
            SynchronizationAnchor(video_timestamp=v, electrical_timestamp=e)
            for v, e in anchors
        ],
        uncertainty_num=uncertainty.numerator,
        uncertainty_den=uncertainty.denominator,
    )


def _proof(
    output_ticks: list[int] | None = None,
    indices: list[int] | None = None,
    *,
    sync: RecordingSynchronization | None = None,
    recording_ticks: list[int] = RECORDING_TICKS,
) -> VideoProvenanceBundle:
    indices = list(range(len(recording_ticks))) if indices is None else indices
    output_ticks = (
        [recording_ticks[index] for index in indices]
        if output_ticks is None
        else output_ticks
    )
    return VideoProvenanceBundle(
        transformations=[
            VideoFrameProvenancePayload(
                source=_timeline(RECORDING_HASH, recording_ticks),
                output=_timeline("b" * 64, output_ticks),
                source_frame_indices=indices,
            )
        ],
        synchronization=_sync() if sync is None else sync,
    )


def _series(
    ticks: list[int] | None = None,
    *,
    time_base_den: int = 10000,
    clock: str = ELECTRICAL_CLOCK,
) -> ElectrosurgicalMeasurementSeries:
    # One sample per millisecond covering video 0..250 ms.
    ticks = list(range(5000, 7510, 10)) if ticks is None else ticks
    return ElectrosurgicalMeasurementSeries(
        source_sha256="c" * 64,
        parser_id="synthetic_csv",
        parser_version="1",
        timestamps=ElectricalTimestampSeries(
            session_id=SESSION,
            clock_id=clock,
            time_base_num=1,
            time_base_den=time_base_den,
            presentation_timestamps=ticks,
        ),
        channels=[
            ElectrosurgicalChannel(
                channel_id="power",
                quantity="power",
                unit="W",
                values=[float(index) for index in range(len(ticks))],
            ),
            ElectrosurgicalChannel(
                channel_id="active",
                quantity="activation",
                unit="1",
                values=[float(index % 2) for index in range(len(ticks))],
            ),
        ],
    )


def _profile(**overrides: object) -> ElectricalFrameAggregationProfile:
    payload: dict[str, object] = {
        "profile_id": "hf_frame_mean",
        "profile_version": 1,
        "max_sample_gap_num": 2,
        "max_sample_gap_den": 1000,
        "max_alignment_uncertainty_num": 1,
        "max_alignment_uncertainty_den": 1000,
        **overrides,
    }
    return ElectricalFrameAggregationProfile.model_validate(payload)


def test_constant_frame_rate_windows_are_half_open_on_pts() -> None:
    result = align_electrosurgical_measurements(
        _proof(), _series(), _profile(), recording_end_timestamp=200
    )

    assert result.status == "complete"
    assert [
        (f.recording_start_timestamp, f.recording_end_timestamp) for f in result.frames
    ] == [(0, 40), (40, 80), (80, 120), (120, 160), (160, 200)]
    first = result.frames[0]
    # [5000, 5400) electrical ticks contains samples 0..39 exactly.
    assert (first.sample_start_index, first.sample_end_index) == (0, 40)
    power, active = first.channels
    assert (power.mean, power.minimum, power.maximum) == (19.5, 0.0, 39.0)
    assert active.mean == 0.5
    # Boundary sample at 5400 belongs to the next frame only.
    assert result.frames[1].sample_start_index == 40
    assert result.generation_content_hash == "b" * 64
    assert result.recording_content_hash == RECORDING_HASH
    assert result.measurement_source_sha256 == "c" * 64


def test_variable_frame_rate_uses_actual_presentation_timestamps() -> None:
    recording = [0, 33, 100, 117, 200]
    result = align_electrosurgical_measurements(
        _proof(recording_ticks=recording),
        _series(),
        _profile(),
        recording_end_timestamp=233,
    )

    counts = [
        (f.sample_end_index or 0) - (f.sample_start_index or 0) for f in result.frames
    ]
    assert all(f.status == "complete" for f in result.frames)
    assert counts == [33, 67, 17, 83, 33]


def test_clock_drift_interpolates_between_anchors_and_inverts_exactly() -> None:
    sync = _sync([(0, 5000), (1000, 15010), (2000, 25000)])

    assert recording_to_electrical_ticks(sync, 500) == Fraction(10005)
    assert recording_to_electrical_ticks(sync, 1500) == Fraction(20005)
    assert electrical_to_recording_ticks(sync, 10005) == 500
    assert electrical_to_recording_ticks(sync, Fraction(15010)) == 1000
    with pytest.raises(ElectricalAlignmentError, match="outside the measured"):
        recording_to_electrical_ticks(sync, 2001)
    with pytest.raises(ElectricalAlignmentError, match="outside the measured"):
        electrical_to_recording_ticks(sync, 4999)


def test_decimation_extends_windows_over_dropped_recording_frames() -> None:
    result = align_electrosurgical_measurements(
        _proof([0, 80, 160], [0, 2, 4]),
        _series(),
        _profile(),
        recording_end_timestamp=200,
    )

    assert [
        (f.recording_start_timestamp, f.recording_end_timestamp) for f in result.frames
    ] == [(0, 80), (80, 160), (160, 200)]
    assert [f.presentation_timestamp for f in result.frames] == [0, 80, 160]


def test_repeated_recording_frames_share_one_window() -> None:
    result = align_electrosurgical_measurements(
        _proof([0, 20, 40, 60, 80], [0, 0, 1, 1, 2]),
        _series(),
        _profile(),
        recording_end_timestamp=200,
    )

    windows = [
        (f.recording_start_timestamp, f.recording_end_timestamp) for f in result.frames
    ]
    assert windows == [(0, 40), (0, 40), (40, 80), (40, 80), (80, 200)]
    assert result.frames[0].channels == result.frames[1].channels


def test_chained_transformations_compose_to_the_recording() -> None:
    first = VideoFrameProvenancePayload(
        source=_timeline(RECORDING_HASH, RECORDING_TICKS),
        output=_timeline("d" * 64, [0, 80, 160]),
        source_frame_indices=[0, 2, 4],
    )
    second = VideoFrameProvenancePayload(
        source=first.output,
        output=_timeline("e" * 64, [0, 1600]),
        source_frame_indices=[1, 2],
    )
    proof = VideoProvenanceBundle(
        transformations=[first, second], synchronization=_sync()
    )

    result = align_electrosurgical_measurements(
        proof, _series(), _profile(), recording_end_timestamp=200
    )

    assert result.generation_content_hash == "e" * 64
    assert [f.recording_frame_index for f in result.frames] == [2, 4]
    assert [f.presentation_timestamp for f in result.frames] == [0, 1600]


def test_missing_terminal_bound_is_explicitly_unbounded() -> None:
    result = align_electrosurgical_measurements(_proof(), _series(), _profile())

    assert result.status == "incomplete"
    last = result.frames[-1]
    assert last.status == "unbounded_interval"
    assert last.recording_end_timestamp is None
    assert last.channels == [] and last.sample_start_index is None


@pytest.mark.parametrize(
    ("proof", "series", "profile", "frame", "status"),
    [
        (
            _proof(sync=_sync([(50, 5500), (1000, 15000)])),
            _series(),
            _profile(),
            0,
            "outside_synchronization",
        ),
        (
            _proof(),
            _series(list(range(5100, 7510, 10))),
            _profile(),
            0,
            "outside_electrical_recording",
        ),
        (
            _proof(),
            _series([*range(5000, 5600, 10), *range(5700, 7510, 10)]),
            _profile(),
            1,
            "sample_gap",
        ),
        (
            _proof(),
            _series(),
            _profile(min_samples_per_frame=41),
            0,
            "insufficient_samples",
        ),
    ],
)
def test_incomplete_windows_report_status_without_values(
    proof: VideoProvenanceBundle,
    series: ElectrosurgicalMeasurementSeries,
    profile: ElectricalFrameAggregationProfile,
    frame: int,
    status: str,
) -> None:
    result = align_electrosurgical_measurements(
        proof, series, profile, recording_end_timestamp=200
    )

    assert result.status == "incomplete"
    assert result.frames[frame].status == status
    assert result.frames[frame].channels == []


def test_gap_straddling_window_start_is_detected() -> None:
    # Samples jump from 5390 to 5420: the window [5400, 5800) begins inside a gap.
    ticks = [*range(5000, 5400, 10), *range(5420, 7510, 10)]
    profile = _profile(max_sample_gap_num=3, max_sample_gap_den=1000)

    result = align_electrosurgical_measurements(
        _proof(), _series(ticks), profile, recording_end_timestamp=200
    )
    assert result.frames[1].status == "complete"

    strict = _profile(max_sample_gap_num=2, max_sample_gap_den=1000)
    result = align_electrosurgical_measurements(
        _proof(), _series(ticks), strict, recording_end_timestamp=200
    )
    assert [f.status for f in result.frames[:2]] == ["sample_gap", "sample_gap"]


def test_bounded_frame_range_selection() -> None:
    result = align_electrosurgical_measurements(
        _proof(),
        _series(),
        _profile(),
        recording_end_timestamp=200,
        first_output_frame=2,
        output_frame_count=2,
    )

    assert [f.output_frame_index for f in result.frames] == [2, 3]
    assert result.status == "complete"


def _align(
    *,
    proof: VideoProvenanceBundle | None = None,
    series: ElectrosurgicalMeasurementSeries | None = None,
    recording_end_timestamp: int = 200,
    first_output_frame: int = 0,
    output_frame_count: int | None = None,
) -> ElectricalVideoAlignment:
    return align_electrosurgical_measurements(
        _proof() if proof is None else proof,
        _series() if series is None else series,
        _profile(),
        recording_end_timestamp=recording_end_timestamp,
        first_output_frame=first_output_frame,
        output_frame_count=output_frame_count,
    )


@pytest.mark.parametrize(
    ("call", "message"),
    [
        (
            lambda: _align(proof=_proof().model_copy(update={"synchronization": None})),
            "synchronization anchors",
        ),
        (lambda: _align(series=_series(clock="4" * 32)), "different session or clock"),
        (lambda: _align(series=_series(time_base_den=1000)), "units differ"),
        (
            lambda: _align(proof=_proof(sync=_sync(uncertainty=Fraction(1, 100)))),
            "uncertainty exceeds",
        ),
        (lambda: _align(recording_end_timestamp=160), "Recording end must follow"),
        (lambda: _align(first_output_frame=5), "outside the video"),
        (lambda: _align(output_frame_count=0), "outside the video"),
    ],
)
def test_alignment_fails_loudly_on_invariant_violations(
    call: Callable[[], ElectricalVideoAlignment], message: str
) -> None:
    with pytest.raises(ElectricalAlignmentError, match=message):
        call()


@pytest.mark.parametrize(
    ("channel", "message"),
    [
        ({"quantity": "power", "unit": "V", "values": [1.0]}, "requires unit W"),
        ({"quantity": "power", "unit": "W", "values": [float("nan")]}, "finite"),
        ({"quantity": "activation", "unit": "1", "values": [0.5]}, "0 or 1"),
        ({"quantity": "impedance", "unit": "Ohm", "values": [-1.0]}, "nonnegative"),
    ],
)
def test_channel_rejects_invalid_values(
    channel: dict[str, object], message: str
) -> None:
    with pytest.raises(ValidationError, match=message):
        ElectrosurgicalChannel.model_validate({"channel_id": "c", **channel})


def test_series_rejects_misaligned_or_duplicate_channels() -> None:
    series = _series([5000, 5010])
    channel = series.channels[0]
    with pytest.raises(ValidationError, match="one value per timestamp"):
        series.model_validate(
            {
                **series.model_dump(),
                "channels": [{**channel.model_dump(), "values": [1.0]}],
            }
        )
    with pytest.raises(ValidationError, match="unique"):
        series.model_validate(
            {
                **series.model_dump(),
                "channels": [channel.model_dump(), channel.model_dump()],
            }
        )
    with pytest.raises(ValidationError, match="increase"):
        _series([5000, 5000])


def test_published_alignment_cannot_claim_completeness_for_incomplete_frames() -> None:
    result = align_electrosurgical_measurements(_proof(), _series(), _profile())
    payload = result.model_dump(mode="json")

    assert (
        ElectricalVideoAlignment.model_validate_json(result.model_dump_json()) == result
    )
    with pytest.raises(ValidationError, match="every frame status"):
        ElectricalVideoAlignment.model_validate({**payload, "status": "complete"})
    tampered = [*payload["frames"]]
    tampered[0] = {**tampered[0], "channels": []}
    with pytest.raises(ValidationError, match="only when complete"):
        ElectricalVideoAlignment.model_validate({**payload, "frames": tampered})
