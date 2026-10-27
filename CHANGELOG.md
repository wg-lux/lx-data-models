# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.4.dev1] - Unreleased

### Added
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

### Changed
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
- `PatientMedicationSchedule`'s create/update/aggregate-create write contracts
  take an ordered list of headed blocks of rows (referencing a medication by
  id or index, or holding a free-text line or compounded-preparation entry)
  instead of a flat list of medication ids/indices.

### Removed
- `PatientMedication.intake_times` and the unstructured `PatientMedication.dosage`
  JSON field, replaced by the structured dosing schedule above.

### Known limitations
- `patient_medication_schedule_from_endoreg` is speculative: the external
  `endoreg_db` Django app has no blocks/rows relation yet matching this
  structure; the adapter documents and expects a provisional shape that does
  not exist until that app grows one.
- This change only makes the internal data model BMP-shaped — it does not yet
  encode or decode the actual BMP carrier-XML/2D-barcode payload. Several BMP
  conformance rules (e.g. mutual exclusivity between coded/free-text fields)
  exist only as documentation in the official XSD, not as machine-checked
  schema constructs; this repo's validators re-implement the ones relevant to
  our own fields, not the full wire format.
- The official Dosiereinheit (dose-unit) code table (33 single-character
  codes mapped to display names) is not in this repo; `unit_code` accepts any
  value matching the expected character class without validating it against
  the real table.
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
- Obtain and wire in the real KBV Dosiereinheit keyword table so `unit_code`
  can be validated/resolved instead of pattern-matched.
- Decide and implement how `endoreg_db` should expose the blocks/rows
  relation `patient_medication_schedule_from_endoreg` currently assumes.
- Decide how/whether BMP's clinical parameters and demographic flags map onto
  `LabValue` or a separate patient-demographics model.
- Reconcile or retire the disconnected `MedicationScheduleReference` catalog
  layer now that `PatientMedication` has its own BMP-shaped dosing.
- Add the corresponding Django-side migrations/fields in `endoreg_db` for the
  new `PatientMedication` attributes and the schedule's blocks/rows structure
  (out of scope for this repo).

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
