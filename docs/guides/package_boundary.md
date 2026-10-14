# Package Boundary Guide

## Host presets and optional employees

For the canonical package layout, field contracts, optional employees, and
validation/import commands, see [Structure of a valid lx-dtypes package](dtypes-package-structure.md).
That guide includes a loadable documentation example and an agent/reviewer
checklist. Reuse the existing ledger `Center` and `Examiner`/`ExaminerDataDict`
contracts; package parsing remains independent of Django setup.

`lx-data-models` should be treated as a package boundary when used from sibling
applications such as `endoreg-db`.

## Rules

- Import through public package modules when an `__init__.py` export exists.
- Do not import test modules, test fixtures, or example scripts from consuming
  applications.
- Keep generated demo artifacts under `temp/generated_exports/` or test-local
  `tmp_path` directories.
- Tests must not write tracked files into repository roots.
- Django ORM models are persistence adapters; cross-service payloads belong in
  Pydantic contracts and package-level interfaces.

## Generated Output Convention

- Example scripts may write to `temp/generated_exports/`.
- Tests should use `tmp_path` and assert on generated files there.
- Golden fixtures, if intentionally committed, should live under explicit test
  data directories rather than package roots.
- Storage ownership, loading and cleanup follow the
  [terminology storage lifecycle](terminology.md#storage-ownership-and-lifetime).
  Shared legacy test exports use process-scoped temporary storage and are cleaned
  at normal interpreter shutdown; new tests should prefer `tmp_path`.

## Test Layout

- Unit tests mirror the production package beneath `tests/unit/lx_dtypes/`.
- Python fixture providers and golden inputs live beneath `tests/fixtures/`.
- Repository-wide integration and package-boundary tests live directly beneath
  `tests/`.
- Test-only Django settings and pytest configuration belong to `tests/`, never
  to the distributable `lx_dtypes` package.

## Raw video identity

Video identity is named `raw_video_hash` across ledger models, processing history,
exports, and hub transfer contracts. Compute it from the original input before
processing. Reimport resolves that same identity even after anonymization,
transcoding, or other image operations change the processed artifact.
`processed_video_hash` verifies a particular processed artifact; it must never
replace the raw identity or determine the resource's transfer key.

This is an intentional breaking field rename from `video_hash`. Payloads must use
`raw_video_hash`; there is no legacy alias. Upgrade producers and consumers
together. The Django RenameField migration preserves existing identity values.

## Unresolved video frame provenance

`VideoProvenanceRecovery` is a separate strict exchange contract from
`VideoProvenanceBundle`. It binds an explicit `unresolved` mapping status to a
recording hash and processed timeline, retains optional original presentation
timestamps and timezone-qualified recording start/end, and permanently sets
`electrical_matching_eligible` to false. It contains no inferred frame indices.
A transfer selects either verified ancestry or an unresolved receipt and must
bind both endpoint hashes. Publishers and receivers must upgrade together;
older strict schemas reject the new field. Persistence, user acknowledgment,
audit and media verification belong to endoreg-db, not this package.
