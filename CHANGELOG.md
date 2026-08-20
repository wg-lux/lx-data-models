# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- A strict `lx-dtypes-kb-registry bootstrap` startup boundary that provisions,
  migrates, and fully validates every packaged knowledge-base identity.

### Changed
- Django application import no longer performs implicit best-effort registry
  seeding; deployments must run the package-owned bootstrap command first.

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
