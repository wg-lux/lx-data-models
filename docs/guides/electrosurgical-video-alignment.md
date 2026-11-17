# Electrosurgical measurements, video alignment, and curve comparison

Owner: lx_dtypes maintainers. This is the canonical guide to the typed
high-frequency (HF) electrosurgical measurement contract, its alignment to
endoscopy video frames, and the knowledge-base and ledger fields for comparing
application curves. Scope and production readiness are tracked only in
endoreg-db `feature-tracking/backlog/ElectricalToVideoMapping.yml`.

## Terms

- **Presentation timestamp (PTS):** the integer display time of a video frame,
  counted in ticks of a rational time base (for example 1/90000 s). PTS define
  frame identity. Nominal frames per second (FPS) are never used for alignment.
- **Sample:** one electrical measurement at one integer tick of the generator's
  clock, which has its own rational time base.
- **Sample rate:** how often a channel is measured. Channels with different
  rates are separate series on the same clock.
- **Clock drift:** the slowly changing rate difference between the video
  recorder clock and the generator clock.
- **Synchronization anchor:** one event observed on both clocks during
  acquisition, stored as a pair of video and electrical ticks.
- **Mapping residuum:** the remaining uncertainty after interpolating between
  anchors. Acquisition supplies it as a conservative bound in seconds.
- **Application:** one maximal run of consecutive samples during which the
  generator reports `activation = 1`, that is, one delivery of HF energy.
- **Phase:** the normalized position within an application, from 0 at its
  first sample to 1 at its last.
- **Multivariate multiple regression:** a linear model that explains several
  response quantities at once from shared predictors, `Y = X B + E`.
- **Mahalanobis distance:** a residual distance scaled by the residual
  covariance, so correlated responses are judged jointly rather than one by one.

## Contracts

| Module | Contract | Purpose |
| --- | --- | --- |
| `contracts/video_provenance.py` | `RecordingSynchronization`, `ElectricalTimestampSeries`, `VideoProvenanceBundle` | Existing anchors, electrical clock ticks and verified frame ancestry. Unchanged hub wire contracts. |
| `contracts/electrosurgical_measurements.py` | `ElectrosurgicalMeasurementSeries`, `ElectrosurgicalChannel` | HF generator values bound to the source file hash, parser version and clock epoch. |
| `contracts/electrical_video_alignment.py` | `ElectricalFrameAggregationProfile`, `ElectricalVideoAlignment`, `align_electrosurgical_measurements` | Versioned, exact frame-level alignment and parameters. |

Each quantity has exactly one Unified Code for Units of Measure (UCUM) unit.
Parsers convert at their boundary; the contract never converts silently.

| Quantity | Unit | Values |
| --- | --- | --- |
| `voltage_peak`, `voltage_rms` | `V` | finite, nonnegative |
| `current_rms` | `A` | finite, nonnegative |
| `power` | `W` | finite, nonnegative |
| `impedance` | `Ohm` | finite, nonnegative |
| `energy` | `J` | cumulative delivered energy, finite, nonnegative |
| `activation` | `1` | `1` while HF energy is delivered, otherwise `0` |

Timestamps within one clock epoch must strictly increase, so duplicate and
non-monotonic samples are rejected. Every channel has exactly one value per
timestamp. A series is limited to 2,000,000 samples and 32 channels. Device
support, channel definitions and clinical parameter approval belong to the
support matrix in the feature definition, not to this package.

## Alignment algorithm `electrical_frame_window_v1`

All arithmetic uses exact fractions; no step rounds a timestamp.

1. **Ancestry.** Verified `source_frame_indices` compose every output frame of
   the published generation back to the original recording frame. An
   unresolved `VideoProvenanceRecovery` is not accepted.
2. **Frame windows on PTS.** An output frame's window starts at its recording
   frame's PTS. It ends at the PTS of the next *distinct* recording frame used by
   a later output frame. Frames that repeat a recording frame share its window.
   Frames dropped by decimation extend the window before them. The last window
   ends at the caller's `recording_end_timestamp` (container origin plus
   duration), or it is reported as `unbounded_interval`.
3. **Clock mapping.** `recording_to_electrical_ticks` interpolates linearly
   between the two neighbouring anchors, which corrects offset and piecewise
   drift. Values outside the first and last anchor are never extrapolated.
   `electrical_to_recording_ticks` is the exact inverse, for plotting electrical
   traces on the video time axis.
4. **Sample assignment.** A sample at electrical tick `t` belongs to a frame when
   `window_start <= t < window_end`. A sample on a boundary belongs to the later
   frame only.
5. **Parameters.** A `complete` window publishes the unweighted mean, minimum
   and maximum of each channel. For `activation`, the mean is the fraction of
   samples with HF energy active.

Window bounds are uncertain by the synchronization uncertainty. Alignment fails
before computing anything when that uncertainty exceeds the profile's
`max_alignment_uncertainty`.

### Frame status

| Status | Meaning | Values |
| --- | --- | --- |
| `complete` | Window covered without gaps and with at least `min_samples_per_frame` samples | yes |
| `outside_synchronization` | Window extends beyond the anchored interval | no |
| `outside_electrical_recording` | Window extends beyond the first or last sample | no |
| `sample_gap` | A sample interval touching the window exceeds `max_sample_gap` | no |
| `insufficient_samples` | Fewer samples than the profile requires | no |
| `unbounded_interval` | Terminal window without a recording end | no |

Missing coverage is never filled with zeros or the last value. The alignment's
`status` is `complete` only when every frame is complete; validation rejects a
payload that claims otherwise.

### Fail-loud errors

`ElectricalAlignmentError` (a `ValueError`) is raised when anchors are missing,
the session, clock or electrical time base differ from the synchronization,
the uncertainty exceeds the profile, the recording end does not follow the last
recording PTS, or the requested frame range lies outside the video.

## Identity binding

`ElectricalVideoAlignment` records the generation content hash and time base,
the recording content hash and time base, the session and electrical clock, the
synchronization method and uncertainty, the measurement source hash, the profile
identity and version, and the algorithm version. A host compares these values
before reuse. A new generation, resampling or another measurement file
therefore requires a new alignment instead of silently reusing an old one.

## Example

```python
from lx_dtypes.models.contracts.electrical_video_alignment import (
    ElectricalFrameAggregationProfile,
    align_electrosurgical_measurements,
)

profile = ElectricalFrameAggregationProfile(
    profile_id="hf_frame_summary",
    profile_version=1,
    max_sample_gap_num=2,          # 2 ms
    max_sample_gap_den=1000,
    max_alignment_uncertainty_num=1,  # 1 ms
    max_alignment_uncertainty_den=1000,
)
alignment = align_electrosurgical_measurements(
    proof,                          # VideoProvenanceBundle with synchronization
    series,                         # ElectrosurgicalMeasurementSeries
    profile,
    recording_end_timestamp=end_tick,
    first_output_frame=0,
    output_frame_count=1500,        # bounded frame range
)
for frame in alignment.frames:
    if frame.status == "complete":
        power = next(c for c in frame.channels if c.quantity == "power")
        print(frame.presentation_timestamp, power.mean)
```

## Application curves and regression comparison

This section defines the knowledge-base and ledger fields that let a ledger
compare one HF application with earlier applications.

| Layer | Record | Purpose |
| --- | --- | --- |
| Knowledge base | `ElectricalCurveProfile` (`model: electrical_curve_profile`) | Versioned curve and regression definition |
| Ledger | `PElectricalApplication` | One complete application as a phase-binned curve with source and clock provenance |
| Ledger | `PElectricalCurveComparison` | Regression of one application against strictly earlier references |
| Functions | `lx_dtypes.stats.electrical_curve` | `extract_application_sections`, `build_electrical_application`, `compare_electrical_application` |

### Profile fields

```{literalinclude} ../examples/dtypes_packages/electrical_curves/profiles.yml
:language: yaml
```

| Field | Contract |
| --- | --- |
| `curve_quantities` | Ordered, unique quantities stored per phase bin; `activation` is not allowed because it defines the application |
| `response_quantities` | Quantities explained by the model; a nonempty subset of the curve quantities |
| `predictor_quantities` | Quantities used as explanatory variables; disjoint from the responses |
| `phase_bins` | Number of equal-width phase bins; must exceed the number of design terms |
| `phase_polynomial_degree` | Phase powers `phase^1 … phase^d` (0 to 5) added after the intercept |
| `min_duration_*`, `max_duration_*` | Rational seconds; applications outside are `too_short` or `too_long` |
| `max_sample_gap_*` | Rational seconds; a larger gap inside an application yields `sample_gap` |
| `min_reference_applications` | At least 2; fewer references fail the comparison |
| `max_mean_mahalanobis_squared` | Deviation threshold for the mean squared residual distance |

The design columns are, in order, `intercept`, the phase powers, and the
predictor quantities. A clinical package must document why its responses,
predictors, and threshold are appropriate; the shipped example is synthetic.

### Extracting applications

`extract_application_sections(series, profile)` requires exactly one
`activation` channel and exactly one channel per curve quantity. It returns
every application with a status; only a `complete` section carries a curve.

| Status | Meaning |
| --- | --- |
| `complete` | Fully recorded, within duration and gap limits, every bin populated |
| `truncated` | The run touches the first or last sample, so its start or end is unknown |
| `sample_gap` | Consecutive samples inside the run are further apart than allowed |
| `too_short`, `too_long` | Duration outside the profile limits |
| `empty_bin` | At least one phase bin received no sample |

Bin `k` of an application from tick `s` to tick `e` holds the samples with
`floor((t - s) * bins / (e - s)) = k`; the last sample belongs to the last bin.
Each bin stores the unweighted mean of each curve quantity and its sample count.
Nothing is interpolated or carried forward.

`build_electrical_application` binds a complete section to its measurement
source hash, session, clock epoch, sample range and the exact profile identity.
Its `started_at` must be timezone-aware and is stored in UTC. Derive it from a
recorded electrosurgery-to-examination `TimeOffset`, not from file timestamps:
it decides which applications count as earlier.

### Comparing with earlier curves

`compare_electrical_application(profile, identity, application, references)`
fits `Y = X B + E` by ordinary least squares on the bins of the reference
applications only. It then scores the compared application:

1. The residual covariance is `S = E'E / (n - p)` for `n` reference bins and
   `p` design terms.
2. For each bin of the compared application, the residual `r = y - x B` gives
   a squared Mahalanobis distance `r' S^-1 r`.
3. The mean over bins is compared with `max_mean_mahalanobis_squared`. If the
   application resembles the references, the mean is close to the number of
   responses; a larger mean yields `deviates`, otherwise `within_reference`.

The result also stores coefficients, the covariance, the reference
coefficient of determination (R², or null for a constant response), and the
per-response root-mean-square error (RMSE) of the compared application.
Validation recomputes the mean and the verdict from the stored values.

The comparison fails with `ElectricalCurveError` when:

- a reference does not start strictly before the compared application;
- references are duplicated or include the application itself;
- there are too few references or too few rows to estimate the covariance;
- predictors are constant or collinear (rank-deficient design);
- the residual covariance is singular.

Every record must also match the same profile name, module and version.
`KnowledgeBase.validate_electrical_observation` resolves that pinned identity
for both ledger records.

The comparison is a statistical similarity measure, not a clinical judgement.
Its validity depends on comparable references, for example the same generator
mode and device class, which the host selects.

## Activation summary CSV exports

Some generators export one summary row per activation instead of sampled
values. `contracts/electrosurgical_activations.py` reads this format:

```text
,t,hfmode,hfmode_options,effect,duration_s,P_avg_W,E_tot_J,slot_number,instrument
3,2000-01-03 09:00:06.000000,endoCUT Q,"interval: 6, duration: 1",3.0,2.1,5.0,11.0,2,Monopolar
```

```python
from lx_dtypes.models.contracts.electrosurgical_activations import (
    read_electrosurgical_activation_csv,
)

log = read_electrosurgical_activation_csv(path, source_timezone="Europe/Berlin")
```

| Column | Field | Rule |
| --- | --- | --- |
| unnamed index | `source_row_index` | Non-negative integer, strictly increasing |
| `t` | `started_at` | Local time of the activation **start**, converted to UTC with `source_timezone` |
| `hfmode`, `hfmode_options` | `mode_label`, `mode_options` | Manufacturer text kept verbatim; empty options become `null` |
| `effect`, `duration_s`, `P_avg_W`, `E_tot_J` | `effect`, `duration_s`, `average_power_w`, `energy_j` | Finite, non-negative `Decimal`; never rounded |
| `slot_number`, `instrument` | same | Integer ≥ 1; non-empty text |

The export has no timezone, so the caller must name the generator clock's zone.
Local times that are skipped or repeated at a daylight-saving change are
rejected. `t` is validated as the start: two activations may not overlap beyond
half the 0.1 s duration resolution. The header must match exactly. Files are
limited to 16 MiB and 100,000 rows. Any error raises
`ElectrosurgicalActivationCsvError` and returns nothing partial.
`source_sha256`, `parser_id` and `parser_version` record provenance.

These rows are summaries, not curves: they cannot feed
`extract_application_sections`. `P_avg_W` is the measured average power, not
the power setting. Mode labels are not mapped to the generic
`electrosurgery_mode` choices, because that mapping is device-specific.

## Boundaries

This package owns only the typed contracts and pure deterministic functions.
Parsing device exports, acquiring anchors, selecting reference applications,
persistence, authorization, API endpoints, pagination, monitoring and
publication belong to the host (endoreg-db). The host's existing nearest-sample selection
`electrical_sample_indices` uses the same anchor interpolation. It can delegate
its clock conversion to `recording_to_electrical_ticks` so that only one mapping
implementation remains.
