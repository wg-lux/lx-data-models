# ColoReg Resection Comparison: Capture and Analysis

Owner: ColoReg study authors; lx_dtypes maintainers own structural validation.
This page is the canonical endpoint and linkage specification for the
`coloreg_resection_comparison` study.

| Item | Value |
| --- | --- |
| Terminology | `coloreg@0.3.0` |
| Report template | `coloreg_colonoscopy@2.0.0` |
| Study document | [`lx_dtypes/data/study_metadata/coloreg_resection.yml`](../../lx_dtypes/data/study_metadata/coloreg_resection.yml) |

The study document holds the four authored hypotheses and the executable
analysis definitions. This page explains what they mean. Cohort authorization
remains a host responsibility, and analyses that depend on protocol decisions
remain drafts.

## Population

The analysis unit is the **index attempted resection of one lesion**. Keep
different lesions and repeat visits distinct.

### Lesion size

| Item | Value |
| --- | --- |
| Classification | `lesion_size_mm` |
| Choice | `lesion_size_oval_mm` |
| Descriptor | `lesion_size_mm_value` |
| Unit | `milimeter` (the existing canonical unit identifier) |
| Threshold | at least 20 mm, inclusive |
| Finding | `colon_polyp`, referenced by `coloreg_index_polyp_finding_id` |

Use the maximum pre-resection diameter at the index examination. Do not select
on the size of a recurrent lesion or on the categorical large-polyp label.
Check that `lesion_size_mm` on the linked resection agrees with the original
polyp measurement. Discrepancies are reported, not resolved silently.

### Technique comparison

The classification `coloreg_resection_technique` defines the compared groups
`coloreg_technique_emr` (EMR) and `coloreg_technique_esd` (ESD).
`coloreg_technique_eftr` (EFTR) can be captured but is excluded from the
primary contrast. After a crossover, keep the primarily attempted technique,
report the completion technique separately, and prespecify the assignment
used for analysis.

Cohort filters only select candidate examinations. The size threshold,
technique groups, and endpoints are expressed separately in
`study_metadata.analysis_definitions` and evaluated on validated lesion units.

## Linkage

| Role | Identifier descriptor |
| --- | --- |
| Case | `coloreg_case_id` |
| Lesion | `coloreg_lesion_id` |
| Index examination | `coloreg_index_examination_id` |
| Index polyp | `coloreg_index_polyp_finding_id` |
| Index resection | `coloreg_index_resection_finding_id` |
| Preceding follow-up | `coloreg_previous_follow_up_examination_id` |

Hosts must:

- Resolve every identifier within the patient authorization that already
  exists. Pseudonymous keys do not grant access.
- Verify that the index polyp finding belongs to the referenced index
  examination, case, and patient.
- Verify that the index resection references the same polyp and lesion. Never
  join only by technique, finding name, or examination.
- Verify that a preceding follow-up belongs to the same lesion and case and
  precedes the current examination. Reject self-links and cycles.
- Order visits by examination timestamps and actual days since the index
  examination, not by report entry order.
- Expect several lesions per case and several examinations per lesion. Avoid
  patient-level or examination-level Cartesian joins.
- Interpret historical observations with the terminology module and version
  recorded on their examination. Do not infer missing historical study fields
  from the currently active package.

Text descriptors only capture the identifiers. Referential integrity, date
ordering, and assembling follow-up history are host responsibilities.

## Captured observations

| Observation | Captured values |
| --- | --- |
| Technique | EMR, ESD, or EFTR, with a separate completion technique and a not-completed state. |
| Instruments | Cold snare, diathermic snare, both, no snare, or unknown. ESD need not use a snare. |
| Electrosurgery | The actual generator and model, current mode, and the settings as labelled by the manufacturer (effect, duration, interval, power with units where shown). No recommended settings or assumed defaults. |
| Success | Primary success is an adjudicated yes, no, or unknown, plus the protocol identifier when adjudicated. Macroscopic completeness, conversion to surgery, and en-bloc, piecemeal, or aborted removal are separate observations. |
| Histology | R0, R1, Rx (not assessable), pending, no specimen, or unknown. Do not infer R0 from en-bloc removal or apparent completeness. |
| Follow-up | Unremarkable, abnormal, not assessable, not performed, or unknown, with first or subsequent visit and an explicit reference to the previous visit. |

Captured complications:

- index perforation
- index bleeding that cannot be controlled endoscopically
- interval bleeding and whether it was controlled endoscopically
- interval perforation
- a repeat examination required because of interval bleeding
- a repeat examination required because of interval perforation
- a post-resection stenosis that cannot be passed at follow-up

## Endpoints

| Endpoint | Classification | Positive | Negative |
| --- | --- | --- | --- |
| Primary success | `coloreg_primary_success` | `yes` | `no` |
| R0 resection | `coloreg_histological_margin_status` | `coloreg_margin_r0` | `coloreg_margin_r1` (assessable only) |
| Follow-up | `coloreg_follow_up_result` | `coloreg_follow_up_unremarkable` | `coloreg_follow_up_abnormal` |
| Complications | see below | `yes` | `no` |

**Primary success** is defined by the study protocol. There is no default
operational definition. An adjudicated result must name its protocol in
`coloreg_primary_success_protocol`.

**R0 resection** counts `coloreg_margin_rx`, `coloreg_margin_pending`,
`coloreg_margin_no_specimen`, and `coloreg_margin_unknown` as separate states,
not as negatives.

**Follow-up** is conditioned on an earlier unremarkable follow-up: compare the
next evaluable visit, and do not preselect the outcome visit to be
unremarkable. Resolve the index resection and all preceding examinations of the
lesion, and take the earlier result from the linked historical record.

**Complications** cover index events (`coloreg_index_uncontrolled_bleeding`,
`coloreg_index_perforation`) and interval events
(`coloreg_interval_uncontrolled_bleeding`, `coloreg_interval_perforation`).
Report bleeding and perforation individually and as an OR composite per index
lesion across the protocol's observation window. Do not double-count an event
that is documented again.

## Analysis requirements

- Require one primarily attempted technique per index lesion. Reject
  conflicting technique selections and unresolved case or lesion links before
  analysis.
- Before analysis, define the primary-success criteria, ascertainment rules,
  follow-up horizon, and eligible follow-up visits. This page deliberately does
  not invent them.
- Prespecify denominators for attempted resections, histologically assessable
  margins, and evaluable follow-up. Report missing data, Rx, pending results,
  and losses to follow-up separately.
- A missing follow-up or an unknown outcome is never an unremarkable result or
  an absence of complications.
- Keep actual eligibility calculations separate from broad candidate cohorts.
  Publish numerator, denominator, and exclusions per endpoint and technique.
- Account for correlated lesions within a patient and for repeated visits.
  Repeated reports are not independent new resections.
- H0 is equal rates and H1 is different rates. These are authored comparisons,
  not evidence that the techniques differ.
- Loading a package does not evaluate a dataset. Hosts explicitly evaluate saved
  analysis definitions against authorized, persisted ledger records and report
  missing records and package-version exclusions.

## Executable analysis

| Component | Implementation |
| --- | --- |
| Contract | `lx_dtypes.models.contracts.study_analysis.StudyAnalysisDefinition` |
| Evaluator | `lx_dtypes.stats.evaluate_study_dataset` |
| Linkage | `lx_dtypes.stats.study_linkage.assemble_coloreg_analysis_units` |
| Authoring | The lx-annotate cohort study-metadata editor. Definitions are stored with the cohort and exported in `StudySetupDefinition` YAML. |

**Input.** A knowledge base validated at its exact version, and ledger
examinations with all their finding occurrences. Hosts supply only authorized
records; unresolved links cannot expand the authorized dataset.

**Unit.** One index resection finding linked to its original polyp, with
optional preceding and outcome follow-up findings. Repeated examinations do not
automatically create new resection units.

**Rules.** Bounded `all`/`any` predicates over classification choices or typed
descriptors, with explicit positive and negative outcomes. Missing inputs stay
unknown, also under negation.

**Status of the four comparisons:**

| Analysis | Status | Required before evaluation |
| --- | --- | --- |
| `histological_r0_emr_vs_esd` | ready | — |
| `primary_success_emr_vs_esd` | draft | The exact identifier and version of an approved primary-success protocol. |
| `follow_up_emr_vs_esd` | draft | Confirmation of the conditioning interpretation and a prespecified follow-up horizon. |
| `complications_emr_vs_esd` | draft | Index-event rules exist. The complete hypothesis needs a defined observation window and longitudinal event aggregation, which the descriptive evaluator does not provide. |

**Results.** Per group: numerator, denominator, negative, missing, ineligible,
unknown-eligibility, and conflicting counts, plus population exclusions and
ambiguous groups. A zero denominator has no rate.

**Histology.** The R0 denominator includes only R0 and R1. Rx, pending, no
specimen, and unknown have separate descriptive counters among documented
margin states. Absent margin observations remain missing.

**Limits.** Versioned rule definitions and typed descriptive results are the
extension point for further statistical methods. This descriptive method does
not reject hypotheses or compute p-values or confidence intervals, and it does
not adjust for clustering within patients.

## Open protocol decisions

The study authors have decided:

- **Hypotheses:** standard H0 (equal rates) and H1 (different rates).
- **Primary success:** defined by the study protocol. No automatic definition
  is supplied.

Still to be confirmed by the study authors:

- **Follow-up conditioning:** the working interpretation is that an earlier
  unremarkable follow-up qualifies the next evaluable visit. Capture supports
  both this analysis and an analysis of all evaluable follow-ups.

## References

- [ESGE colorectal polypectomy and EMR guideline, 2024 update](https://www.esge.com/assets/downloads/pdfs/guidelines/2024_a-2304-3219.pdf):
  terminology for resection techniques, en-bloc removal, histological R0, and
  delayed adverse events. It does not define this study's primary-success
  endpoint.
