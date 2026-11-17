from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import numpy as np
import pytest
from pydantic import ValidationError

from lx_dtypes.models.contracts.electrical_curve import (
    ElectricalApplicationCurve,
    ElectricalCurveRegressionResult,
)
from lx_dtypes.models.contracts.electrosurgical_measurements import (
    ElectrosurgicalChannel,
    ElectrosurgicalMeasurementSeries,
)
from lx_dtypes.models.contracts.knowledge_base import KnowledgeBaseIdentity
from lx_dtypes.models.contracts.package_snapshot import (
    PackageSnapshot,
    build_package_snapshot,
    restore_package_snapshot,
)
from lx_dtypes.models.contracts.video_provenance import ElectricalTimestampSeries
from lx_dtypes.models.interface.data_formats import read_record, write_record
from lx_dtypes.models.interface.KnowledgeBase import KnowledgeBase
from lx_dtypes.models.interface.Ledger import Ledger
from lx_dtypes.models.knowledge_base.electrical_curve_profile import (
    ElectricalCurveProfile,
)
from lx_dtypes.models.ledger.p_electrical_application import (
    PElectricalApplication,
    PElectricalCurveComparison,
)
from lx_dtypes.packages import load_package
from lx_dtypes.stats.electrical_curve import (
    ElectricalCurveError,
    build_electrical_application,
    compare_electrical_application,
    extract_application_sections,
    fit_and_score_curves,
)

EXAMPLE = Path("docs/examples/dtypes_packages/electrical_curves/config.yaml")
PROFILE = "synthetic_cut_impedance_response"
START = datetime(2026, 1, 1, tzinfo=UTC)

# (first sample index, duration in samples, power scale); one sample per ms.
NORMAL_RUNS = [(10, 400, 1.0), (500, 350, 1.0), (1000, 450, 1.0), (1600, 380, 1.0)]


@pytest.fixture(scope="module")
def kb() -> KnowledgeBase:
    return load_package(EXAMPLE)


@pytest.fixture(scope="module")
def profile(kb: KnowledgeBase) -> ElectricalCurveProfile:
    return kb.electrical_curve_profile[PROFILE]


@pytest.fixture(scope="module")
def identity(kb: KnowledgeBase) -> KnowledgeBaseIdentity:
    return kb.config.knowledge_base_identity


def _series(
    runs: list[tuple[int, int, float]],
    *,
    total: int = 2200,
    seed: int = 7,
    ticks: list[int] | None = None,
) -> ElectrosurgicalMeasurementSeries:
    """Synthetic generator: impedance rises during a cut; current follows V/Z."""
    rng = np.random.default_rng(seed)
    ticks = list(range(total)) if ticks is None else ticks
    activation = [0.0] * len(ticks)
    impedance = [1000.0] * len(ticks)
    current = [0.0] * len(ticks)
    power = [0.0] * len(ticks)
    for first, length, scale in runs:
        for offset in range(length):
            index = first + offset
            phase = offset / length
            z = 100 + 300 * phase + 40 * phase**2 + float(rng.normal(0, 5))
            i = 200 / z + float(rng.normal(0, 0.01))
            activation[index] = 1.0
            impedance[index] = z
            current[index] = i
            power[index] = scale * 200 * i + float(rng.normal(0, 2))
    return ElectrosurgicalMeasurementSeries(
        source_sha256=f"{seed:064x}",
        parser_id="synthetic_generator",
        parser_version="1",
        timestamps=ElectricalTimestampSeries(
            session_id="1" * 32,
            clock_id="2" * 32,
            time_base_num=1,
            time_base_den=1000,
            presentation_timestamps=ticks,
        ),
        channels=[
            ElectrosurgicalChannel(
                channel_id="active", quantity="activation", unit="1", values=activation
            ),
            ElectrosurgicalChannel(
                channel_id="z", quantity="impedance", unit="Ohm", values=impedance
            ),
            ElectrosurgicalChannel(
                channel_id="i", quantity="current_rms", unit="A", values=current
            ),
            ElectrosurgicalChannel(
                channel_id="p", quantity="power", unit="W", values=power
            ),
        ],
    )


def _applications(
    profile: ElectricalCurveProfile,
    identity: KnowledgeBaseIdentity,
    runs: list[tuple[int, int, float]],
    *,
    seed: int = 7,
    day: int = 0,
) -> list[PElectricalApplication]:
    series = _series(runs, seed=seed)
    sections = extract_application_sections(series, profile)
    assert [section.status for section in sections] == ["complete"] * len(runs)
    return [
        build_electrical_application(
            series,
            section,
            profile,
            identity,
            patient_examination=f"exam-{seed}",
            started_at=START
            + timedelta(days=day, milliseconds=section.start_timestamp),
        )
        for section in sections
    ]


def test_profile_loads_exports_and_survives_snapshots(
    kb: KnowledgeBase, profile: ElectricalCurveProfile, tmp_path: Path
) -> None:
    assert profile.design_terms == ["intercept", "phase^1", "phase^2", "impedance"]
    exported = kb.export_record_lists()["electrical_curve_profiles"]
    assert exported[0]["name"] == PROFILE
    snapshot = build_package_snapshot(kb)
    restored = restore_package_snapshot(
        PackageSnapshot.model_validate_json(snapshot.model_dump_json())
    )
    assert (
        restored.electrical_curve_profile[PROFILE].model_dump() == profile.model_dump()
    )
    path = tmp_path / "profile.yml"
    write_record(ElectricalCurveProfile, profile, path)
    assert (
        read_record(ElectricalCurveProfile, path).model_dump() == profile.model_dump()
    )


def test_packages_without_profiles_keep_snapshot_identity() -> None:
    # A package without electrical profiles, snapshotted before the family existed.
    other = load_package(
        Path("docs/examples/dtypes_packages/time_references/config.yaml")
    )
    payload = build_package_snapshot(other).model_dump(mode="json")
    assert payload["records"]["ElectricalCurveProfile"] == []
    payload["records"].pop("ElectricalCurveProfile")

    legacy = PackageSnapshot.model_validate(payload)

    assert legacy.snapshot_id == build_package_snapshot(other).snapshot_id
    assert not restore_package_snapshot(legacy).electrical_curve_profile


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ({"curve_quantities": ["power", "activation"]}, "Activation defines"),
        ({"response_quantities": ["energy"]}, "must be curve quantities"),
        ({"predictor_quantities": ["power"]}, "both response and predictor"),
        ({"phase_bins": 4}, "must exceed the number of design terms"),
        ({"max_duration_num": 1, "max_duration_den": 100}, "below the minimum"),
        ({"curve_quantities": ["power", "power"]}, "unique"),
    ],
)
def test_profile_rejects_inconsistent_definitions(
    profile: ElectricalCurveProfile, payload: dict[str, object], message: str
) -> None:
    data = {**profile.model_dump(exclude={"uuid", "created_at"}), **payload}
    with pytest.raises(ValidationError, match=message):
        ElectricalCurveProfile.model_validate(data)


def test_sections_are_activation_runs_with_explicit_status(
    profile: ElectricalCurveProfile,
) -> None:
    runs = [(0, 300, 1.0), (400, 50, 1.0), (600, 300, 1.0), (1000, 300, 1.0)]
    ticks = list(range(2200))
    # Remove 20 ms inside the third run: larger than the 10 ms gap limit.
    ticks = [tick for tick in ticks if not 700 <= tick < 720]
    series = _series(
        [
            (first if first < 700 else first - 20, length, scale)
            for first, length, scale in runs
        ],
        total=len(ticks),
        ticks=ticks,
    )
    sections = extract_application_sections(series, profile)

    assert [section.status for section in sections] == [
        "truncated",
        "too_short",
        "sample_gap",
        "complete",
    ]
    complete = sections[-1]
    assert complete.curve is not None
    assert complete.curve.quantities == ["current_rms", "impedance", "power"]
    assert sum(complete.curve.bin_sample_counts) == 300
    assert complete.end_timestamp - complete.start_timestamp == 299
    assert all(section.curve is None for section in sections[:-1])


def test_long_and_sparsely_binned_sections(profile: ElectricalCurveProfile) -> None:
    long = extract_application_sections(_series([(10, 5200, 1.0)], total=5300), profile)
    assert [section.status for section in long] == ["too_long"]

    sparse_profile = profile.model_copy(
        update={"min_duration_num": 1, "min_duration_den": 1000}
    )
    # Samples every 8 ms inside the 10 ms gap limit leave some 5 ms bins empty.
    ticks = [*range(100), *range(100, 150, 8), *range(150, 300)]
    activation_start = 100
    series = _series([(activation_start, 7, 1.0)], total=len(ticks), ticks=ticks)
    sections = extract_application_sections(series, sparse_profile)
    assert [section.status for section in sections] == ["empty_bin"]


def test_series_without_unique_channels_is_rejected(
    profile: ElectricalCurveProfile,
) -> None:
    series = _series(NORMAL_RUNS)
    duplicate = series.model_copy(
        update={
            "channels": [
                *series.channels,
                series.channels[1].model_copy(update={"channel_id": "z2"}),
            ]
        }
    )
    with pytest.raises(ElectricalCurveError, match="exactly one impedance"):
        extract_application_sections(duplicate, profile)


def test_ledger_records_round_trip_and_validate_against_kb(
    kb: KnowledgeBase,
    profile: ElectricalCurveProfile,
    identity: KnowledgeBaseIdentity,
    tmp_path: Path,
) -> None:
    references = _applications(profile, identity, NORMAL_RUNS)
    current = _applications(profile, identity, [(100, 420, 1.0)], seed=11, day=1)[0]
    comparison = compare_electrical_application(profile, identity, current, references)
    for record in (*references, current, comparison):
        kb.validate_electrical_observation(record)

    ledger = Ledger(
        electrical_applications={str(a.uuid): a for a in (*references, current)},
        electrical_curve_comparisons={str(comparison.uuid): comparison},
    )
    records = ledger.export_record_lists()
    assert "p_electrical_applications" in records
    assert "p_electrical_curve_comparisons" in records
    assert len(records["p_electrical_applications"]) == 5
    assert (
        PElectricalCurveComparison.model_validate(
            records["p_electrical_curve_comparisons"][0]
        )
        == comparison
    )
    assert PElectricalApplication.model_validate(current.serialized_ddict) == current
    path = tmp_path / "ledger.yml"
    write_record(Ledger, ledger, path)
    restored = read_record(Ledger, path)
    assert restored.electrical_applications == ledger.electrical_applications
    assert restored.electrical_curve_comparisons == ledger.electrical_curve_comparisons

    for field, value in [
        ("knowledge_base_version", "2.0.0"),
        ("knowledge_base_module", "other"),
        ("electrical_curve_profile", "missing"),
    ]:
        with pytest.raises(ValueError):
            kb.validate_electrical_observation(
                current.model_copy(update={field: value})
            )


def test_regression_separates_typical_and_deviating_applications(
    profile: ElectricalCurveProfile, identity: KnowledgeBaseIdentity
) -> None:
    references = _applications(profile, identity, NORMAL_RUNS)
    typical = _applications(profile, identity, [(100, 420, 1.0)], seed=11, day=1)[0]
    deviating = _applications(profile, identity, [(100, 420, 1.5)], seed=12, day=1)[0]

    within = compare_electrical_application(profile, identity, typical, references)
    deviates = compare_electrical_application(profile, identity, deviating, references)

    assert within.result.verdict == "within_reference"
    assert deviates.result.verdict == "deviates"
    assert deviates.result.mean_mahalanobis_squared > 10 * (
        within.result.mean_mahalanobis_squared
    )
    assert within.result.reference_row_count == 40
    assert within.result.design_terms == profile.design_terms
    r_squared = [
        value for value in within.result.reference_r_squared if value is not None
    ]
    assert len(r_squared) == 2 and min(r_squared) > 0.9
    assert within.reference_applications == [str(a.uuid) for a in references]
    # Deterministic: identical inputs give identical results.
    again = compare_electrical_application(profile, identity, typical, references)
    assert again.result == within.result


def test_comparison_requires_earlier_unique_references(
    profile: ElectricalCurveProfile, identity: KnowledgeBaseIdentity
) -> None:
    references = _applications(profile, identity, NORMAL_RUNS)
    current = _applications(profile, identity, [(100, 420, 1.0)], seed=11, day=1)[0]

    with pytest.raises(ElectricalCurveError, match="Too few reference"):
        compare_electrical_application(profile, identity, current, references[:2])
    with pytest.raises(ElectricalCurveError, match="strictly earlier"):
        compare_electrical_application(
            profile, identity, references[0], [current, *references[1:]]
        )
    with pytest.raises(ElectricalCurveError, match="unique"):
        compare_electrical_application(
            profile, identity, current, [references[0], *references[:3]]
        )
    with pytest.raises(ElectricalCurveError, match="own reference"):
        compare_electrical_application(
            profile, identity, current, [current, *references]
        )
    with pytest.raises(ValueError, match="exact KB definition identity"):
        compare_electrical_application(
            profile,
            KnowledgeBaseIdentity(
                knowledge_base_module="electrical_curves",
                knowledge_base_version="2.0.0",
            ),
            current,
            references,
        )


def test_degenerate_reference_designs_fail_loudly(
    profile: ElectricalCurveProfile,
) -> None:
    def curve(impedance: float, offset: float) -> ElectricalApplicationCurve:
        return ElectricalApplicationCurve(
            quantities=["current_rms", "impedance", "power"],
            bin_values=[
                [1.0 + offset + 0.1 * k, impedance, 200.0 + 3 * k - offset]
                for k in range(10)
            ],
            bin_sample_counts=[5] * 10,
        )

    constant = [curve(100.0, offset) for offset in (0.0, 0.1, 0.2)]
    with pytest.raises(ElectricalCurveError, match="rank deficient"):
        fit_and_score_curves(profile, constant[0], constant)

    with pytest.raises(ValueError, match="phase bins disagree"):
        fit_and_score_curves(
            profile,
            ElectricalApplicationCurve(
                quantities=["current_rms", "impedance", "power"],
                bin_values=[[1.0, 1.0, 1.0]] * 3,
                bin_sample_counts=[1] * 3,
            ),
            constant,
        )


def test_published_result_must_match_its_own_statistics(
    profile: ElectricalCurveProfile, identity: KnowledgeBaseIdentity
) -> None:
    references = _applications(profile, identity, NORMAL_RUNS)
    current = _applications(profile, identity, [(100, 420, 1.0)], seed=11, day=1)[0]
    result = compare_electrical_application(
        profile, identity, current, references
    ).result
    payload = result.model_dump()

    with pytest.raises(ValidationError, match="Verdict disagrees"):
        ElectricalCurveRegressionResult.model_validate(
            {**payload, "verdict": "deviates"}
        )
    with pytest.raises(ValidationError, match="Mean distance disagrees"):
        ElectricalCurveRegressionResult.model_validate(
            {**payload, "mean_mahalanobis_squared": result.mean_mahalanobis_squared + 1}
        )
    with pytest.raises(ValidationError, match="one row per term"):
        ElectricalCurveRegressionResult.model_validate(
            {**payload, "coefficients": payload["coefficients"][:-1]}
        )
