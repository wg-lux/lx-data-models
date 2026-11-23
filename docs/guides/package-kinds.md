# Package kinds and package channels

Every knowledge-base package can declare what it contains. Hosts use the kind to
offer only fitting packages, for example only `report_templates` packages in a
reporting package selector.

## Kinds

| `package_kind` | Contains | May depend on |
| --- | --- | --- |
| `terminology` | Clinical concepts: findings, classifications, examinations, units, interventions, indications, validators, time references, electrical curve profiles | `terminology`, `application_data` |
| `report_templates` | Report templates, sections and reporting validators | `terminology`, `report_templates`, `application_data` |
| `study` | Study metadata, presets and analyses | `terminology`, `report_templates`, `application_data` |
| `application_data` | Endoreg application and reference data: labels, genders, centers, workforce, hardware | `application_data` |

`PackageKind` is exported from `lx_dtypes` and `lx_dtypes.models.contracts`.
`package_kind_dependency_allowed(kind, dependency_kind)` evaluates the table.

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
