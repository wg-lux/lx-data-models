# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.7.4]

### Added
- `scripts/kb_catalog.py` for terminology maintainers: `status` diagnoses every
  catalog release with a fix for each problem, `new-version` retains the
  published bytes and dependencies of a default release and starts a new
  version, and `refresh-digest` updates unreleased digests only.
- Retained release bundles, including their snapshotted dependency modules, are
  pinned in `tests/fixtures/lx_dtypes/retained_release_bundles.json`; tests
  resolve every shipped release through the provider registry and refuse
  tampered installs.
- [Terminology releases](docs/guides/terminology-releases.md) guide with the
  release workflow and an integrity error reference.

### Changed
- Integrity errors for packaged knowledge bases, registry digests, identity
  conflicts, missing versions and unresolved template validators now explain
  how to fix them, for both host operators and terminology maintainers. Message
  prefixes are unchanged. New public helpers:
  `lx_dtypes.knowledge_bases.published_release_remediation` and
  `registered_digest_remediation`.
- Current deployment templates select `endoreg_reference@2.0.0`, whose clinical
  definitions are owned by terminology dependencies. Schema migration preserves
  existing package version pins.
- Application-data packages may depend on terminology without owning its
  clinical concepts. Information-source identities formerly embedded in the
  reference catalogue are provided by `endoreg_information_sources@1.0.0`.

### Fixed
- Reference vocabulary checks resolve the current catalogue through the package
  loader, and source provenance includes the extracted information-source package.

## [0.7.2]

### Added
- `lx-dtypes-release prepare X.Y.Z` sets the version in `pyproject.toml`,
  `CITATION.cff` (with its release date), the `CHANGELOG.md` heading and
  `uv.lock`. `lx-dtypes-release check-version` reports files that disagree.
- Localized `display_names` mappings in runtime validator results, preserving
  stable machine identifiers for consumers.
- FHIR terminology export and import cover examination indications as the
  `lx-indication-cs` CodeSystem and `lx-indication-vs` ValueSet, so host FHIR
  exports can code `Procedure.reasonCode` against a published CodeSystem.
  Terminology Bundles therefore contain two more resources.

### Changed
- Report-template structure and readiness messages use the requested language
  and localized concept names, including German rule-evaluation output.
- Source distributions include only the library and release metadata. CI and
  publishing run the release helper's artifact verification before publication.
- Consolidated study metadata and ColoReg resection guidance into Markdown,
  with a standalone YAML example for study label presentation.
- Package kinds stay separate: a package's own records must belong to its kind
  (`PACKAGE_KIND_OWN_MODELS`), and `application_data` reference catalogs may not
  carry terminology concepts (`TERMINOLOGY_REFERENCE_MODELS`). Breaches are the
  lint error `package_kind_content_violation`, without exceptions, which new
  imports and registered reads reject; packages without a declared kind are
  checked against the kind their records imply.
- The training preset example ships its employee list as a separate
  `training_staff` application-data package referenced through `depends_on`,
  instead of selecting it as a data file of the study preset.

### Fixed
- `CITATION.cff` cited version 0.2.20 instead of the current release.
- Examination and indication catalog routes (`examinations/`,
  `examinations/{id}/`, `examinations/{id}/indications/`) no longer fail with
  HTTP 500 when the host stores `NULL` localized names; such names now fall back
  to the semantic name like empty ones.
- Ledger payloads built from the host (`build_p_examination_payload_from_host_ledger`)
  now include the patient examination's indications and their chosen
  classification options as `patient_indications`. Before, saved indications were
  missing from the record, so required indication concepts such as
  `koloskopie.indikation` always validated as missing. Hosts without an
  `indications` relation contribute no indications; a row without an
  indication name is rejected. A chosen option is attributed to the one
  classification it shares with its indication (hosts such as endoreg-db link
  choices many-to-many); a choice that resolves to none or several
  classifications is rejected.
- FHIR terminology export failed with "duplicate concept codes" for every
  package depending on `lx_units`, because `lx_units` defined both
  `liters-per-minute` and `liters_per_minute`. The duplicate is removed and the
  `supplemental_oxygen_flow_rate_value` descriptor uses `liters-per-minute`.
  `lx_units` and `lx_descriptors` keep version 0.1.0 with new content digests
  in `catalog.json`. Registries that already installed the previous 0.1.0
  content keep it and must have those entries replaced by an operator; retained
  releases `coloreg` 0.1.0/0.2.0 and `dgvs_reporting` 0.1.0 embed the old
  definitions and still cannot be exported as FHIR terminology.

## [0.7.1]

### Added
- Package kinds, deterministic `lx-package.json` manifests, shared legacy-kind
  inference, and verified package-channel installation.
- Package-kind provenance in terminology listings and dependency-kind validation.
- A "Public API" reference page and docstrings for every name exported from
  `lx_dtypes`, `lx_dtypes.evaluation`, and `lx_dtypes.packages`.
- An HTTP API reference generated from the OpenAPI schema, and the schema
  itself as `openapi.json` in the built documentation. Every operation now has
  an OpenAPI description stating its authentication and error responses.

### Changed
- Deployment setup schema 2.0 separates reference, terminology, report-template,
  and study package roles. Schema 1.0 remains readable for explicit migration;
  consumers must migrate setup documents and regenerate their deployment locks.
- Report-template validation resolves named validators within the dependency
  closure and rejects ambiguous duplicate definitions.

## [0.6.7] - Unreleased

### Added
- Shared `report_medications` and `report_electrosurgery` report sections. Templates
  list them in `report_sections` and declare the package in `depends_on`.
- Electrosurgery terminology: status and repeatable application findings with mode,
  power setting (W), activation duration (s), delivered energy (J) and curve
  comparison. Adds the `watt` and `joule` units.
- `dgvs_reporting@0.2.0`: the colonoscopy template includes the medication and
  electrosurgery sections and their completeness validators.
- `ElectrosurgicalMeasurementSeries`, PTS-based frame alignment
  (`align_electrosurgical_measurements`), the `ElectricalCurveProfile` KB record,
  `PElectricalApplication`/`PElectricalCurveComparison` ledger records and their
  multivariate regression comparison.
- `read_electrosurgical_activation_csv` for per-activation generator CSV exports;
  the source timezone must be named explicitly.
- Validation code `terminology.electrical_curve_profile_unknown`.

### Changed
- Classification validator hints may include `descriptor_free_choice_names`. A
  selected choice without descriptors (for example a bolus) now satisfies a
  required classification; descriptor-backed choices still need their value.
- Identity mismatches for time offsets and electrical observations raise
  `SemanticValidationError("terminology.identity_mismatch")` with one message.
- `LedgerRecordList.p_indications` is typed `SerializedPIndicationDataDict`.
- `KB_MODEL_NAMES_ORDERED`/`L_MODEL_NAMES_ORDERED` are derived from their `Literal`;
  record-list exports are generated from the registries. Output is unchanged.
- Removed the unused `LedgerBaseModel.serialized_model_cls`/`serialized_ddict_cls`
  class attributes. Ledger models with nested records override
  `serialized_model_class()`/`serialized_ddict_class`, the single mechanism.

### Fixed
- Exporting a ledger whose indications carry classifications no longer fails.
- `LedgerDataDict` declares the `examiners` collection the `Ledger` model has.

### Retained
- The published `dgvs_reporting@0.1.0` and its dependency closure are kept unchanged
  under `data/terminology/versions/dgvs_reporting/0.1.0/` for pinned examinations.

## [0.5.4.dev1] - Unreleased

### Added
- Shared model policies in `lx_dtypes.models.model` and canonical strict/advisory
  Python and JSON entry points in `lx_dtypes.evaluation`. Legacy validation,
  numeric classification and electrical-alignment imports remain available.
- A checked YAML inventory of model policy exceptions and structural outliers,
  enforced by pytest and the pre-commit quality gate.
- `PatientMedication` carries BMP-aligned fields: an optional PZN, up to three
  ordered active substances with strengths, a structured dosing schedule
  (day-segment quantities, an optional once-weekly weekday, or free text), a
  dosage form (coded or free text), a dose-unit code alongside the existing
  unit, and separate usage-notes and bound-continuation-line fields distinct
  from the existing treatment-reason field.
- `PatientMedicationSchedule` models an ordered, headed sequence of medication
  blocks, each holding medication entries, compounded-preparation entries, or
  free-text lines — matching the German "Bundeseinheitlicher Medikationsplan"
  (BMP) medication-table structure.
- A reusable `MedicationEntryFields`/`MedicationDosingSchedule`/
  `MedicationSubstance`/`MedicationScheduleHeading` family of shared contract
  types backs both the read ledger model and the write contracts.
- A generic `json_encoded_fields()` hook on `LedgerBaseModel` serializes
  structures that mix nested ledger references with inline value objects.
- A technical specification summary of the BMP v2.8 carrier-XML format,
  derived from the official KBV agreement, its annexes, the real XSD, and a
  sample instance.
- `project_emp_entry()` projects a `PatientMedication` onto the gematik ePA
  Medication Service 1.3.5 electronic medication plan (eMP): an `emp-medication`
  Medication and an `emp-medication-request` MedicationRequest with
  `DosageDgMP`/`TimingDgMP` dosing, plus `$add-emp-entry` and `$update-emp-entry`
  Parameters builders. Entries that cannot be represented without inference
  raise `EpaProjectionError`.
- `lx_dtypes.models.contracts.german_fhir` provides KVNR and PZN check-digit
  validation (`Kvnr`, `Pzn`) and German base-profile system URIs.
- `lx_dtypes.models.contracts.kbv_key_tables` carries the KBV
  `S_BMP_DOSIEREINHEIT` V1.01 and `S_KBV_DARREICHUNGSFORM` V1.16 key tables.
- `lx_dtypes.stats.standardized` writes complete, manifest-hashed CSV exports of
  the knowledge base, examination ledger, cases, video segments and their states,
  medical ledgers, image and box annotations, and a `frames` table whose
  `export_path` locates frame images bundled through `write_csv_tables(files=...)`.
- `lx_dtypes.django.standardized_export` exports explicitly selected Django
  querysets (all concrete fields and many-to-many links, on the queryset's own
  database) without writes. Binary columns require `binary="base64"`; querysets
  that repeat a record through a join fail until `.distinct()` is applied.

- `lx_dtypes.models.contracts.text_embedding` defines versioned embedding spaces,
  finite nonzero vectors with same-space cosine similarity, and
  `ReportConceptSpan`, an annotation request that references a report span by
  source hash and offsets and cannot carry free text or vectors.

### Fixed
- `PatientVideoFile.serialized_model` no longer fails for every video: the
  serialized form now declares its anonymization state, segment UUID references
  and sensitive-metadata UUID reference. Sensitive metadata is never inlined.

### Changed
- Package-owned object models now reject unknown fields unless they explicitly
  declare an extension/projection policy. The previously implicit cases are
  enumerated in `docs/model-boundaries.yml`; clients must remove unsupported
  fields. Explicit coercion, mutability and wire serialization remain unchanged.
- Pydantic KB, ledger and combined registries no longer load Django adapters.
  `VideoFileDjango` is available through the Django registry rather than the
  Pydantic lookup. Production-local test harnesses moved into the repository test
  tree, with framework doubles isolated in their required subprocess.
- Report anonymization v2 requires typed extraction evidence and owner-bound
  staging receipts. Provider failure is distinct from valid empty extraction;
  deterministic fallback preserves its actual backend and bounded failure code.
- Producers and hosts must upgrade together; v1 payloads fail closed. This local
  prerelease candidate is not a published release.
- `PatientMedication.medication` (trade/display name) is now optional: an
  entry may instead be identified by PZN and/or active substances, per BMP's
  data-minimization convention. A medication entry must still set at least
  one identifying or descriptive field.
- `PatientMedication.medication_indication` is now length- and
  line-break-constrained to match BMP's treatment-reason field.
- `PatientMedication.pzn` now rejects values with an invalid PZN check digit.
- `PatientMedicationSchedule`'s create/update/aggregate-create write contracts
  take an ordered list of headed blocks of rows (referencing a medication by
  id or index, or holding a free-text line or compounded-preparation entry)
  alongside the existing flat medication ids/indices; a request must choose one shape.

### Compatibility
- Legacy `dosage`, `intake_times`, flat schedule membership and write references
  remain supported without inferred clinical conversion. BMP dosing cannot be
  combined with populated legacy dosage/intake fields.
- EndoReg stores ordered plan blocks as validated JSON references to canonical
  patient medication rows. The adapter checks complete membership and ownership.
  Apply the corresponding EndoReg migration before using the new fields.

### Known limitations
- This change only makes the internal data model BMP-shaped — it does not yet
  encode or decode the actual BMP carrier-XML/2D-barcode payload. Several BMP
  conformance rules (e.g. mutual exclusivity between coded/free-text fields)
  exist only as documentation in the official XSD, not as machine-checked
  schema constructs; this repo's validators re-implement the ones relevant to
  our own fields, not the full wire format.
- The eMP projection does not cover BMP headings, free-text lines, or
  compounded-preparation rows, ICD-10-GM reason codes, or ATC/ASK codings, and
  its rendered dosage text is not the HL7 Deutschland reference algorithm.
- The pre-existing, disconnected catalog layer (`MedicationScheduleReference`
  and related types in `contracts/reference_catalog.py`) still models dosing
  as a clock-time regimen and was intentionally left untouched — it now
  diverges further from `PatientMedication`'s BMP-shaped dosing.
- `LabValue` models were explicitly out of scope for this change; BMP's three
  clinical parameters (weight/height/creatinine) and its pregnant/
  breastfeeding/sex/allergy flags have no home in this repo yet.

### Follow-up work
- Implement BMP carrier-XML encode/decode (the 2D-barcode payload) on top of
  this data model.
- Validate generated eMP Parameters with the HL7 FHIR validator against
  `de.gematik.epa.medication#1.3.5` in CI.
- Decide how/whether BMP's clinical parameters and demographic flags map onto
  `LabValue` or a separate patient-demographics model.
- Reconcile or retire the disconnected `MedicationScheduleReference` catalog
  layer now that `PatientMedication` has its own BMP-shaped dosing.


## [0.2.37] - 2026-09-08

### Added
- An independently versioned `coloreg` knowledge-base package with a published
  colonoscopy template and Paris/NICE-only polyps.
- A strict `lx-dtypes-kb-registry bootstrap` startup boundary that provisions,
  migrates, and fully validates every packaged knowledge-base identity.
- Revisioned compare-and-swap terminology selection with inter-process writer
  serialization and deterministic conflict responses.

### Changed
- Runtime relationship and state checks now raise `ValueError` under normal and
  optimized Python. Unsupported descriptor creation fails before input lookup.
- Registry bootstrap validates artifacts in-process with fresh loaders.
- Remote branches and tags are downloaded on resolution and cached by archive
  content; full commit SHA URLs reuse cached snapshots without downloading.
  Incomplete or unsafe cache entries are rebuilt after replacement validation.
- Runtime YAML loading parses once and rejects duplicate mapping keys with source
  locations. Lint discovery scans overlapping module roots once per invocation.
- `serialization.model_lookup` remains importable as an empty compatibility module;
  lookup ownership remains with `models.knowledge_base.knowledge_base_models_lookup`.
- Django application import no longer performs implicit best-effort registry
  seeding; deployments must run the package-owned bootstrap command first.
- Report-template reads and mutations now require an explicit knowledge-base
  version and reject mismatched loaded or payload identities.
- Terminology import no longer changes the deployment-global active selection.
- Versioned knowledge-base resolution no longer falls back to installed package
  data when no registry or explicit input directories are configured.

## [0.2.17] - 2026-08-13

### Added
- Canonical Django migration `0005_videofiledjango` for the concrete
  `VideoFileDjango` model exported by the package.
- Release artifacts are rejected when their migration filenames, contents, or
  declared maximum differ from the source tree.
- A strict, versioned `PatientExaminationReportDraft` contract for canonical
  report-editor JSON persistence across lx-annotate and endoreg-db.
- Strict knowledge-base, AI-dataset, application-settings, core-concept, and
  persisted LXDM boundary contracts with deterministic round-trip validation.
- Localized examination and indication catalog DTOs, plus versioned German and
  English report-template titles and section titles.
- A maintained data-model concept map covering contracts, knowledge-base
  models, ledger records, host integration, and persistence ownership.

### Changed
- Release preparation keeps Python distribution versions separate from
  knowledge-base module identities and ignores historical artifacts in reused
  local `dist/` directories.
- Report-template responses preserve their resolved knowledge-base module and
  version, and the compiler carries localized titles through to consumers.
- Wheel and source-distribution validation now requires the complete packaged
  knowledge-base data tree and a usable German reporting template.

## [0.2.14] - 2026-08-11

### Added
- Project metadata reshaped for eventual PyPI publication.
- Development dependency group separated from runtime requirements.
- A public, complete `DtypesRecordPersistencePayload` contract and JSON
  parse/dump helpers for Django host persistence boundaries.
- An installed-wheel release check that verifies the packaged
  `upper_gi_quality_2025` and `colonoscopy_training_basic` report templates are
  published and production-ready.

### Changed
- LXDM record persistence now covers the complete `PExamination` ledger graph;
  unknown root and nested fields are rejected instead of being silently kept.
- Patient-finding deletion requires host authentication and object authorization,
  records actor/time provenance, and refreshes the persisted LXDM record atomically.
- Report-template lifecycle mutations now resolve the active writable module and
  version used by runtime discovery, while immutable templates installed from the
  Python package fail closed instead of being modified in `site-packages`.
- Release metadata checks now use a pinned Twine version that accepts the
  metadata format emitted by the pinned build toolchain.

## [0.1.0] - 2025-12-10

### Added
- Initial public packaging baseline.

## [0.1.1] - 2026-03-15
### Fixing Mypy Errors
- Typed compatibility aggregation in `lx_dtypes.models.main` for shared model/type aliases.

### Changed
- Reworked package-level exports in `lx_dtypes/__init__.py` to lazy import behavior to avoid eager Django model loading during settings/plugin initialization.
- Updated Hatch build include configuration in `pyproject.toml` to use standard TOML tables (`[tool.hatch.build.targets.*.force-include]`) instead of multiline inline tables.

### Fixed
- Resolved Ruff/pre-commit configuration parse failures caused by invalid multiline inline TOML tables.
- Resolved mypy-django plugin startup crash (`AppRegistryNotReady`) by removing import-time Django model side effects from package init.
- Resolved strict mypy issues in report-template validator and runtime modules (alias covariance, typed dict casting, literal narrowing, and loop variable type separation).
- Resolved strict mypy issues in parser and test fixtures (typed dict key completeness, concrete dict generics, and enum-typed adapter test inputs).
- Resolved strict mypy issues in dynamic host-model API tests by removing invalid static type assumptions for runtime-imported ORM models.
- Added django-stubs-compatible generic annotations for KB `ManyToManyField` declarations with `TYPE_CHECKING` model imports across unit, intervention, information_source, indication, finding, and classification_choice Django model modules.
- Added a mypy-safe Ninja API typing shim in `lx_dtypes/django/api/main.py` (typed decorator protocol, `Schema` type-check alias, explicit return annotations/casts, and `urls` protocol support) to satisfy strict checks without runtime behavior changes.
- Brought `pre-commit run mypy --all-files` to passing state.
