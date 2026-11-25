# Package kinds and package channels

Every knowledge-base package can declare what it contains. Hosts use the kind to
offer only fitting packages, for example only `report_templates` packages in a
reporting package selector.

This page is the canonical contract. Host-specific behavior is described in
endoreg-db (`docs/package_kinds_host_guide.md`: what the database does with each
kind) and lx-annotate (`docs/guides/package-kinds.md`: where each kind appears in
the application).

## Choosing a kind

A package has exactly one kind, chosen by **what its own records are** and
**who owns their meaning**. Everything else is referenced through `depends_on`.

Ask in this order and stop at the first "yes":

1. Does it define report templates or report sections? Use `report_templates`.
2. Does it define clinical concepts or rules (findings, classifications,
   examinations, indications, interventions, units, validators)? Use
   `terminology`.
3. Does it define a study preset? Use `study`.
4. Does it provide host reference data (centers, labels, staff, hardware,
   medications, sustainability catalogues)? Use `application_data`.
5. Does it need records from several of these answers? Split it into several
   packages linked by `depends_on`.

| Kind | Use it when the package… | Do not use it for… | Shipped examples |
| --- | --- | --- | --- |
| `terminology` | defines the shared clinical vocabulary and its rules: findings, classifications and choices, examinations, indications, interventions, units, descriptors, validators | report layout, host configuration, study protocols | `lx_findings`, `lx_units`, `coloreg_terminology`, `DGVS_Terminology` |
| `report_templates` | defines how a report is structured: templates, sections, report findings and template-specific validators, built on terminology | defining shared clinical concepts (put them in a terminology package; local concepts only trigger a warning) | `coloreg`, `dgvs_reporting`, `report_medications`, `report_electrosurgery` |
| `study` | defines a study preset: how a study provisions centers, genders, labels and the examinations it uses | clinical definitions, staff lists, report layout | the `training_preset` documentation example |
| `application_data` | provides reference data the host application needs to run: centers, labels and label sets, genders, AI model metadata, medications, workforce, hardware, sustainability catalogues | any clinical concept that terminology already defines (examinations, findings, classifications, indications, interventions, information sources, units) | `endoreg_workforce`, `endoreg_green_endoscopy`, `endoreg_reference` |

Rules of thumb:

- **One owner per concept.** A clinical concept is defined in exactly one
  terminology package. Report templates, studies and application data refer to
  it through `depends_on`; they never carry a copy.
- **Ask who approves a change.** Clinical meaning (a new classification choice)
  is reviewed by clinical owners and belongs in terminology. Report wording and
  layout belong in report templates. Site setup (a new center, a staff list)
  belongs in application data.
- **Mixed content means more than one package.** For example, a study preset
  that needs an employee list depends on a separate `application_data`
  package (see the `training_preset` and `training_staff` example), and a
  report template that needs a new finding depends on a terminology package
  that defines it.
- **Activate report templates, register everything else.** Hosts activate one
  `report_templates` package for reporting. Terminology, application data and
  study packages are registered and used through dependencies, deployment roles
  or explicit host commands.
- **Declare the kind.** Set `package_kind` in `config.yaml`. An undeclared
  package is still checked against the kind its records imply, but declared
  kinds make listings, selectors and deployment roles unambiguous.

Common mistakes and how the lint reports them:

| Mistake | Diagnostic | Fix |
| --- | --- | --- |
| Clinical concepts inside an `application_data` reference catalog | `package_kind_content_violation` | Move them to a terminology package and depend on it |
| Validators in a `study` or `application_data` package | `validators_in_package_kind` | Move them to terminology or report templates |
| Records of several kinds in one package | `package_kind_content_violation` | Split the package |
| Terminology depending on report templates or a study | `package_kind_dependency_violation` | Reverse the dependency; terminology is the base layer |
| Declared kind differs from the reviewed catalog kind | `package_kind_conflict` | Correct the declaration |

## Kinds

| `package_kind` | Contains | May depend on |
| --- | --- | --- |
| `terminology` | Clinical concepts: findings, classifications, examinations, units, interventions, indications, validators, time references, electrical curve profiles | `terminology`, `application_data` |
| `report_templates` | Report templates, sections and reporting validators | `terminology`, `report_templates`, `application_data` |
| `study` | Study metadata, presets and analyses | `terminology`, `report_templates`, `application_data` |
| `application_data` | Endoreg application and reference data: labels, genders, centers, workforce, hardware | `application_data`, `terminology` |

`PackageKind` is exported from `lx_dtypes` and `lx_dtypes.models.contracts`.
`package_kind_dependency_allowed(kind, dependency_kind)` evaluates the table.

## Kinds stay separate

A package's own records (its root and `modules`, never `depends_on`) must belong
to its kind; `PACKAGE_KIND_OWN_MODELS` in `lx_dtypes.package_kinds` lists them.
Content of another kind is referenced through `depends_on` instead.

- `application_data` reference catalogs may not carry terminology concepts
  (examinations, examination types, indications, findings, classifications and
  their choices and types, interventions, information sources, units;
  `TERMINOLOGY_REFERENCE_MODELS`). Otherwise a host receives two competing
  definitions of one clinical concept.
- `report_templates` packages may still define local terminology; that is
  reported by the separate report-template concept warning.
- A package without a declared or reviewed kind is checked against the kind its
  own records imply, so omitting `package_kind` never bypasses the rule.

Breaches are `package_kind_content_violation` lint errors without exceptions:
new imports and registered reads reject them. Move clinical definitions into
terminology packages and reference them through `depends_on`.

## Declaring the kind

Add an optional top-level scalar to `config.yaml`:

```yaml
name: training_terminology
version: "1.0.0"
package_kind: terminology
```

Any other value is a validation error. An absent value means **unclassified**.
There is no default kind: unclassified packages stay registrable, loadable and
selectable as before, and listings report `package_kind: null`. Consumers show
them as unclassified and do not offer them in kind-specific selectors.

Shipped releases declare their kind in `lx_dtypes/data/catalog.json`; their
published `config.yaml` bytes are unchanged. The installed catalog must classify
every entry. A shipped `config.yaml` that declares a kind must match the catalog.

## Package manifest `lx-package.json`

`export_package`, `export_package_files` and `package_archive_bytes` write a
root `lx-package.json` when the root `config.yaml` declares a kind:

```json
{
  "name": "training_terminology",
  "package_kind": "terminology",
  "schema": "lx-package/1",
  "version": "1.0.0"
}
```

The content is generated deterministically (`LxPackageManifest.to_json_bytes`).
An `lx-package.json` already present in the package root must agree with
`config.yaml` and is rewritten in this canonical form; a disagreeing copy fails
the export.

`read_package_archive`, `import_package` and `TerminologyService.import_zip`
compare a present manifest with the root `config.yaml` (`name`, `version`,
`package_kind`) and reject any mismatch before anything is published. ZIPs
without the manifest remain importable as legacy shares; their kind is the one
declared in `config.yaml`, if any.

## Legacy migration

`infer_legacy_package_kind(source, *, input_dirs=None)` (exported from
`lx_dtypes` and `lx_dtypes.packages`) applies one shared rule to a loaded
`KnowledgeBase` or a root `config.yaml` path (loaded through `load_package`).
It returns `PackageKindInference(package_kind, reason)`. Only the package's own
records count: the root module and the modules it composes through `modules`;
records reached through `depends_on` are ignored. Folder names are never used.

1. Any `report_template` or `report_template_section` record: `report_templates`.
2. Otherwise only terminology records (units, descriptors, choices,
   classifications, findings, examinations, indications, interventions,
   citations, information sources, the five validator models, time references
   and electrical curve profiles): `terminology`.
3. Otherwise only `reference_catalog` or `center_employee_list`: `application_data`.
4. Otherwise only `study_preset`: `study`.
5. Anything else, including mixes, `report_finding` alone or no records: `None`.

The library never writes an inferred kind into package files or the registry.

## Registry listings

`TerminologyService.list_bundles()` and the Ninja route
`GET /terminology/bundles` include `package_kind` and `package_kind_source` for
every bundle (also in the report-template catalog):

| `package_kind_source` | Meaning |
| --- | --- |
| `declared` | Registry entry written by a ZIP import, or the local `config.yaml` |
| `catalog` | Unmodified shipped provenance classified in `catalog.json` |
| `migrated` | Not declared; inferred on the fly from locally available sources |
| `null` | Unclassified (`package_kind` is also `null`) |

Conflicting declarations fail with HTTP 409. Remote sources are never fetched
for a listing, and unloadable bundles stay unclassified. Hosts decide whether to
persist a migrated kind. Selection and activation semantics are unchanged.

## Validators

`terminology` packages may carry validator records as the central consensus;
`report_templates` packages may carry their own custom validators. Template
validator names (`validators.*_validators`) resolve within the package and its
dependency closure; an unresolved name fails loading. Any repeated validator
name in one resolved closure, identical or not, fails loading (the existing
duplicate-definition rule), so a divergent rule needs its own name. `study` and
`application_data` packages carry no validators.

## Channel index `channel.json`

A package channel is a static, read-only directory:

```text
<channel-root>/
  channel.json
  packages/<sha256-of-zip-bytes>.zip
```

`PackageChannelIndex` validates `channel.json` (`schema: lx-package-channel/1`).
Entries (`PackageChannelEntry`) carry `name`, `version`, `package_kind`,
lowercase `sha256`, positive `size`, `path` equal to `packages/<sha256>.zip`
and UTC `published_at`. Unknown fields, duplicate identities and duplicate bytes
are rejected.

`lx_dtypes` does not fetch anything. A host fetches the bytes and calls:

```python
from lx_dtypes.packages import install_channel_package

result = install_channel_package(entry, payload, service=service)
```

It checks `size` and `sha256`, requires an `lx-package.json` matching the entry,
then imports through `service.import_zip`. It never selects or activates the
package. Packages are not patient data and must never contain patient data.

## Dependency audit

`audit_package_kind_dependencies(config_path, input_dirs=..., package_kinds=...)`
reports each dependency edge that violates the table (`violation`) or involves an
unclassified module (`unclassified`). `audit_packaged_kind_dependencies()` audits
all shipped releases with the catalog kinds; they have no violations. The package
lint (`check_kb_package`, the `ok` CLI and the authoring gate behind
`load_package`, import and export) enforces the rules as errors whenever both
kinds are known, from `config.yaml` or the reviewed catalog. Edges involving an
unclassified module are not errors.
