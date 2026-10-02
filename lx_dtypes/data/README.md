# Packaged definitions

Maintained by the lx-dtypes maintainers. The structural contract is documented in
[Structure of a valid lx-dtypes package](../../docs/guides/dtypes-package-structure.md).
The machine-readable inventory is [definitions.yml](definitions.yml).

- **`study_metadata/`** contains portable study documents. `research.yml` uses
  `StudySetupDefinition`: datasets, cohorts and study eligibility metadata belong
  here. Validate it with `parse_study_setup_yaml`; do not pass it to the KB loader.
- **`terminology/`** contains versioned knowledge-base packages: concepts, units,
  classifications, examinations, report templates and reference catalogues.
  Each package selects its records through `config.yaml`. Module identity is its
  declared name and version, independent of the enclosing directory.
- **`catalog.json`** selects published terminology releases and records their
  integrity digests. Historical releases remain under `terminology/versions/`.

Report templates and executable numeric rules are terminology contracts, even
when authored for a particular study. Host reference catalogues such as workforce
and sustainability definitions are also terminology; they are not cohort metadata.
Annotation mappings and numeric rules are separate sidecars, not ordinary KB lists.
Study metadata must not be added to a terminology manifest's selected data files.
No participating centres, age limits or eligibility rules should be inferred from
clinical concept names; these require an authored study protocol.

Legacy CSV exports have moved to `demo-data/legacy_exports/`; they are not packaged
reference definitions. Unfinished authoring examples live under `demo-data/drafts/`.
Log scaffolding lives under `tests/fixtures/lx_dtypes/logs/`.

## Path migration

Former `data/<package>/` paths are now `data/terminology/<package>/`.
The former `data/terminology/config.yaml` aggregator is now
`data/terminology/DGVS_Terminology/config.yaml`; its existing child packages retain
their paths. `data/study_setup/research.yml` is now
`data/study_metadata/research.yml`. Update filesystem/resource consumers to these
paths. Public Python imports, module identities, release versions and catalogued
package digests are unchanged. Existing registry copies are not moved automatically.

A package that loads is structurally supported; this does not establish clinical
approval or successful downstream database projection. For registration and
publication, follow the [authoring guide](../../docs/guides/knowledge-base-authoring.md).

## ColoReg resection study

`coloreg@0.3.0` supplies reporting template `coloreg_colonoscopy@2.0.0` for
lesion-linked resection and longitudinal follow-up. The published `0.2.0` package
and its dependency closure remain under `terminology/versions/coloreg/0.2.0/`.
The [study document](study_metadata/coloreg_resection.yml) stores the four
comparison hypotheses separately from terminology. The canonical
[endpoint and linkage specification](../../docs/guides/coloreg-resection-study.yml)
explains protocol-defined primary success, denominators and host responsibilities.
