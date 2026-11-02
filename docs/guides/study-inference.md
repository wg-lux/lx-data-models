# Configured study inference

The canonical contracts are `StudyAnalysisDefinition` and `StudyInference` in
`lx_dtypes.models.contracts.study_analysis`; execution is local through
`evaluate_study_dataset`. Scope and verification belong to
[endoreg-db feature tracking](../../../../endoreg-db/feature-tracking/DtypesStudyDefinitions.yml),
criterion `configured_statistical_inference`.

Study setup YAML stores `variables` and `inference` inside each
`study_metadata.analysis_definitions` entry. The study editor exposes the same
fields. Save the cohort, reload it, then explicitly run its statistics action.
The server reads authorized persisted ledgers; browser-supplied observations
or calculated results are not accepted. Use the exact registered terminology
version and real numeric classification descriptors. Binary endpoints remain
supported, but a numeric-only analysis may use `endpoints: []`.

Each variable has `name`, `role`, `classification`, and `descriptor`. Roles use
the existing index/polyp/follow-up linkage. Each inference has `name`, `method`,
`outcome` (a variable name), `alpha` (strictly between zero and one), and
`missing` (`error` by default or explicitly `complete_case`). Configure:

| Method | Additional configuration | Estimate |
| --- | --- | --- |
| `welch_t_test` | `groups`: two distinct configured group names | First group mean minus second |
| `paired_t_test` | `paired_variable`: another numeric variable | Outcome minus paired measurement |
| `linear_regression` | `predictors`: distinct numeric variable names | Ordinary least squares coefficients with an intercept |

The unused method fields must stay empty. The editor clears them when changing
methods. Group/population rules apply before inference. Paired tests preserve
both measurements from the same linked analysis unit; complete-case exclusion
removes the whole pair. Regression excludes a row only when complete-case
handling is explicitly selected and a required outcome or predictor is missing.
Missing and complete observation counts accompany every result.

All methods require one analysis unit per patient. Repeated lesions or repeated
index visits are rejected rather than silently treated as independent samples.
This release does not aggregate patients or fit clustered/mixed models. Follow-up
measurements require existing verified linkage; they are never paired by row order.

Tests are two-sided with unadjusted p-values. Confidence intervals use `1-alpha`.
Welch does not assume equal group variances. Paired inference assumes independent
patient differences; ordinary least squares coefficient inference assumes
independent homoskedastic errors. Distributional assumptions must be checked in
the study protocol; the program does not certify them or automatically confirm
a clinical hypothesis. Categorical encoding, interactions, robust covariance,
multiple-testing adjustment and missing-value imputation are not implicit.

Results include degrees of freedom, estimates, standard errors, t statistics,
p-values and confidence intervals; regression adds R squared, and Welch adds
group counts. Insufficient samples, nonfinite values, zero sampling variance,
rank-deficient designs and regression with zero residual variance fail explicitly.
Definitions and their digest identify the calculation configuration. Empty numeric
configuration is omitted from serialization to preserve existing descriptive
analysis and setup identities. Upgrade
shared contracts and consumers together; older strict consumers reject new fields.

Numerical implementation uses NumPy least squares and SciPy Student-t distribution.
Reference tests compare independent/paired results against SciPy and regression
against a known orthogonal design:
[SciPy Welch test](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.ttest_ind.html),
[SciPy paired test](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.ttest_rel.html),
[NumPy least squares](https://numpy.org/doc/stable/reference/generated/numpy.linalg.lstsq.html).


## YAML-driven scatter and forest plots

Criterion `configured_dataset_plots` in the same feature tracker owns this scope.
Add `plots` to an analysis in the study setup YAML before importing it through
`import_study_setup` or the setup-import API. This is study setup configuration,
not a new terminology record family. Existing `load_base_db_data`/reference-catalog
provisioning supplies annotation `Label` names; setup import validates references
against those loaded names rather than creating labels implicitly.

`plots.labels` is a nonempty list (maximum 50). Each entry has a unique display
`name`, a `source` and an exact `reference`:

| Source | Reference | Observation semantics |
| --- | --- | --- |
| `endpoint` | A configured analysis endpoint name | Reuses its positive, negative, eligibility and missingness rules |
| `image_annotation` | A dataloader-provisioned label name | Positive if any eligible frame has a true annotation; negative only if recorded annotations are all false; otherwise missing |
| `video_annotation` | A dataloader-provisioned label name | Positive if a validated segment carries the label; no such segment means missing, never an inferred negative |

Set `plots.limit` to 1–5000 (default 1000). Numeric axes come from the existing
analysis `variables` list; configure at least two for scatter plots. The browser
provides dropdowns for source, label, group and both axes, using those YAML names.
Selections change the local view, not the saved study rules. Imported plot
configuration survives saving from the study editor and YAML download.

Each point represents one included index finding. Annotation evidence is linked
to that finding's examination and is restricted to authorized cohort examinations,
selected dataset videos, consistent patient/center links and anonymized processed
media. The response contains numeric values, configured label states and group
names, but no patient, examination, finding or media identifiers. Hover text shows
values and states. The bounded scatter projection takes the first included units
in the existing stable evaluation order, not a random sample. Omitted points and
missing axis values among transmitted points are displayed separately.

The label forest plot uses the full included population, regardless of the scatter
limit or axis missingness. Rows show the positive proportion among explicitly
positive and negative observations, unknown counts, and 95% Wilson intervals.
Repeated patient units suppress intervals across this analysis; descriptive rates
remain visible. Empty denominators have no estimate or interval. Video-label
absence cannot establish a negative denominator, so inspect the unknown counts.
Intervals describe label presence, not causal effects or comparisons between groups.
The inference result panels additionally show coefficient/mean-difference forest
plots using the server's existing estimates and confidence intervals, with a zero
reference line. Accessible data tables accompany forest plots.

Wilson intervals use [SciPy proportion_ci](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats._result_classes.BinomTestResult.proportion_ci.html).

## Categorical comparisons and diagnostic accuracy

Criterion `categorical_diagnostic_evaluation` in the same feature YAML owns this
extension. Add `categorical` to an analysis definition alongside `endpoints`.
Endpoint names refer to the existing validated positive, negative and eligibility
rules. Configure through the categorical section of the study editor or YAML;
save and reload before running statistics. The dataloader/setup import retains
these settings. No observations or calculated counts are accepted from the browser.

```yaml
categorical:
  - name: primary_comparison
    method: fisher_exact
    endpoint: primary_outcome
    groups: [intervention, control]
    design: cohort
    alpha: 0.05
    missing: error
  - name: diagnostic_validation
    method: diagnostic_accuracy
    endpoint: index_test_positive
    reference: reference_standard_positive
    alpha: 0.05
    missing: complete_case
```

This fragment requires those endpoints and groups to be defined in the same
analysis, using the study's registered terminology. It is not a standalone
terminology package. `chi_square` is the other comparison method. Comparison
configuration requires exactly two distinct groups and an explicit `design`:
`cohort` (also appropriate for randomized trials) or `case_control`. Diagnostic
configuration instead requires a distinct reference endpoint, with no comparison
groups or design field. There is no inferred reference standard or threshold.

Comparison table rows follow the configured group order; columns are positive,
negative. Ratios compare group 1 with group 2. Both methods return conditional
maximum-likelihood odds ratios with exact conditional confidence intervals.
Cohort designs also return risk ratios with Katz log intervals; case-control
sampling does not establish risks, so those results omit risk ratios. These are
unadjusted associations, not covariate-adjusted causal estimates.

Pearson chi-square uses one degree of freedom and no Yates correction. Every
expected cell count must be at least five; sparse tables fail with a recommendation
to configure Fisher explicitly. Fisher uses the two-sided fixed-margin exact test.
Comparisons require nonempty row and column margins. Neither method adds a
continuity correction to zero cells. Tests report unadjusted p-values; selecting
several endpoints does not apply a multiplicity correction.

Diagnostic rows are index-test positive/negative and columns are reference-standard
positive/negative: `[[true positive, false positive], [false negative, true negative]]`.
Both endpoint states come from the same authorized linked analysis unit. Sensitivity,
specificity, positive and negative predictive values, and accuracy have Wilson
intervals at `1-alpha`. Predictive values and accuracy depend on the sampled
population and its prevalence; selected case-control samples are not automatically
representative clinical validation cohorts. Diagnostic estimation has no hypothesis
test or p-value. Verification bias and reference-standard quality need protocol review.

All methods require one analysis unit per patient, checked before missingness
exclusion. At least two complete units are required. Unknown, conflicting,
ineligible and eligibility-unknown endpoint states never become negatives. The
default `missing: error` rejects them; explicit `complete_case` excludes the entire
unit and reports the excluded count. Existing descriptive endpoint results retain
state-specific counts, which can be consulted for the reasons. Comparisons select
only the configured two groups; diagnostic estimation uses all included groups.
This release does not support clustered observations or paired group comparisons.

Zero denominators yield an undefined diagnostic estimate with a reason. Infinite
ratio estimates or interval limits are encoded as `null` with an explicit
“Unbounded” note; undefined values have an “Undefined” note. No nonfinite JSON
numbers or artificial zero-cell counts are emitted. The UI shows oriented counts,
exclusions, interval methods, tables and forest plots. Ratio plots use a reference
line at one; diagnostic plots use the proportion scale from zero to one.

Calculations use the existing SciPy dependency:
[contingency chi-square](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.chi2_contingency.html),
[Fisher exact](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.fisher_exact.html),
[conditional odds ratio](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.contingency.odds_ratio.html),
and [relative risk](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.contingency.relative_risk.html).
Empty categorical configuration is omitted from definition serialization to
preserve existing definition digests. As with numeric inference, shared contracts
and consumers must be released together; older strict consumers reject new fields.
