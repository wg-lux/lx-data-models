# Structure of a valid lx-dtypes package

This is the canonical structural guide for humans and agents authoring versioned
lx-dtypes terminology packages, including endoreg-db presets. It is maintained
by the lx_dtypes maintainers. The executable example is under
`docs/examples/dtypes_packages/training_preset/`; all its records are synthetic
and must not be treated as clinical defaults.

For publishing and deployment, see [Knowledge-Base Authoring](knowledge-base-authoring.md).
For application boundaries, see [Package Boundary Guide](package_boundary.md).
Implementation/readiness evidence belongs to endoreg-db's
`feature-tracking/DataLoading.yml` and `feature-tracking/DtypesStudyDefinitions.yml`,
not this document.

## Start here: your first study package

A study package is a versioned folder of YAML definitions. It describes what
your registry study records and which terminology or validation rules apply.
Each participating centre can store the same approved package in its own
location. Package identity is its **name and version**, not its installation
path. Patient observations belong in the host application's ledger, not in
these package files.

| You want to… | Use |
| --- | --- |
| Define terminology, examinations, report templates, or validation rules | A package with `config.yaml` and selected `.yml` records |
| Store packages in a location chosen by your application | `TerminologyService` with an explicit registry path and `register_local()` |
| Upload a portable package through lx-annotate | The terminology ZIP upload workflow; selection is a separate step |
| Choose a centre and approved packages for endoreg-db | A deployment setup `.yml` document; see “Deployment setup v1” below |
| Define datasets or cohorts | A separate `StudySetupDefinition` document |
| Check patient observations without interrupting capture | The [advisory validation API](cross-layer-validation.md#advisory-validation-during-data-capture) |

For the first exercise, use the supplied `training_preset@1.0.0` example.
It contains a synthetic centre and examination, with no clinical validation
rules. Successfully loading it proves the package structure works; it does not
make it an approved study protocol.

1. Copy `docs/examples/dtypes_packages/training_preset/` to a writable authoring
   location. Keep its folder name and `config.yaml` unchanged for this exercise.
2. Open the `.yml` files in a text editor. Use spaces for indentation and preserve
   the field names. The sections below explain each record.
3. Validate and register the copied directory with the command below.
4. Have the clinical study owner review the real terminology and validation
   rules before publishing your own named and versioned package.
5. Ask the host administrator to select and, where needed, project the approved
   package into the application. Registration alone does neither.

With `lx-dtypes` installed in the host's Python environment, run this command,
replacing both absolute paths with your own locations:

```sh
lx-dtypes-kb-registry register-local /srv/register-study/terminology/registry.json \
  --module training_preset --version 1.0.0 \
  --input-dir /srv/register-study/packages/training_preset
```

The command validates the exact identity and its selected files before updating
the registry. It prints the registered identity with `is_active: false` for a
new registration and exits with status `0`. Repeating the same registration is
safe. Invalid data, missing dependencies, or an identity already registered at
another location fail with a nonzero status. Existing registrations and active
selection are preserved. Registration does **not** copy or modify your package,
create database rows, or hydrate the shipped catalogue.

For a package with dependencies, repeat `--input-dir` for their source roots,
or select one release tree containing all required modules. Avoid a broad parent
directory containing several releases of the same module. Every process using
the registry must be able to read the registered paths.

## Choose where packages live

There are three different locations; they need not be siblings:

| Location | Purpose | Example |
| --- | --- | --- |
| Package directory | `config.yaml` and its selected data; may be on a read-only mounted release volume | `/srv/study-releases/training_preset` |
| Registry file | Maps exact identities to package source directories | `/var/lib/study-host/terminology/registry.json` |
| Upload directory | Managed copies produced by ZIP imports, derived from the registry parent | `/var/lib/study-host/terminology/terminology-packages` |

Absolute paths belong in deployment configuration and registry entries. Inside
the package manifest, use relative paths so the same release works at every
centre. Local registration is suitable for application-owned storage and mounted
release directories. ZIP import is suitable when the application should manage
the installed copy. Both use the same loader and identity checks.

For Python callers, pass one service throughout the operation:

```python
from pathlib import Path
from lx_dtypes.terminology.terminology_service import TerminologyService
from lx_dtypes.terminology.terminology_loader import load_module_kb, resolve_module_path

service = TerminologyService(
    registry_path=Path("/var/lib/study-host/terminology/registry.json"),
)
service.register_local(
    "training_preset",
    "1.0.0",
    input_dirs=[Path("/srv/study-releases/training_preset")],
)
kb = load_module_kb("training_preset", version="1.0.0", service=service)
source = resolve_module_path("training_preset", version="1.0.0", service=service)
print(kb.config.knowledge_base_identity.canonical_name, source)
```

An explicit `service=` takes precedence over the global host service: these calls
do not read `TERMINOLOGY_ROOT` or `LX_DTYPES_KB_REGISTRY`, select another registry,
or fall back to shipped data. Missing registrations and unavailable source paths
are errors. Separate services can coexist in the same process without changing
settings or environment variables. `active_kb_identity(service=service)` reads
that registry's selection; prefer explicit versions for historical examinations.

### Existing lx-annotate and endoreg-db deployments

lx-annotate sets Django's `TERMINOLOGY_ROOT` from
`endoreg_db.utils.paths.get_runtime_paths().terminology`. Endoreg-db's package
import and deployment services consume this shared terminology service. Keep
that host-owned path as the authority for the running application; do not add
a second path calculation in each importer.

Existing calls without `service=` keep using the configured host service. A
custom importer, test, or study administration utility can pass an explicit
service when it intentionally manages a different registry. To make a local
registration visible in the normal application, register it in the **same
registry file the application's service uses**. A registry in your working
directory does not configure the host. The host administrator can inspect it
with `get_terminology_service().registry_path` in the configured Django shell.

`LX_DTYPES_KB_REGISTRY` belongs to the standalone resolver API; it does not
redirect the host's `TerminologyService`. Setting it is not a substitute for
configuring the host runtime paths. See [Terminology configuration](terminology.md)
for initialization, cache behavior, and shared-worker access.

## Coordinate a multi-centre release

The coordinating centre publishes one reviewed package name, version, and
content. Each participating centre registers that release at its own local
location and retains its own immutable centre key. Agree on terminology names,
required observations, units, and validation rules before deployment.

Record the package identity alongside each examination. Keep historical
versions available, and use a new package version for protocol changes. A
registry identity does not by itself prove byte-for-byte content equality:
endoreg-db deployment planning records a digest of the dependency closure in
its reviewed lock, and apply checks that content again. The local registration
command validates the source but does not pin a content digest or make the
source immutable. Use read-only release storage and the host's reviewed
deployment workflow for operational studies.

Each centre's deployment `.yml` selects the same approved package versions and
its own `site.center_key`. Paths and patient data remain local. Selecting a
package, importing reference records, creating cohorts, and granting user access
are distinct host operations. Advisory validation can highlight missing study
observations while capture continues; it does not replace structural validation
or the host's rules for finalizing records.

For the training exercise, copy this site document and change `site` for the
second centre. Keep it outside `training_preset/`, and register the package in
each centre's registry before resolving the setup. `activate: false` leaves the
active selection unchanged. This setup does not import the preset's centres or
create a dataset; use the separate host projection commands below when needed.

```{literalinclude} ../examples/dtypes_packages/training_centre.yml
:language: yaml
```

The deployment resolver produces the same package-content digest for identical
release bytes at different paths. Site settings are recorded separately in each
deployment lock. A changed package file changes the digest, even if its author
forgot to increase the package version.

## Deployment configuration and package authoring

A deployment setup document selects already registered package identities and
the site's center. A package's `config.yaml` selects the data files that define
that package. Keep these documents separate: deployment setup is not a KB record
and must not be placed inside a package's selected `data.files` or `data.dirs`.

Clinical changes belong in a new version of the owning package. Site selection
does not rename clinical concepts, rewrite historical references, or supply
arbitrary Django model names. Employee records remain optional and use the
separate contract described below. Neither document grants patient access.

The host YAML authoring guide (`docs/wiki/dataloader_yaml_authoring.md` in the
`endoreg-db` repository) owns deployment commands, database reconciliation, and
recovery procedures.
This guide owns package structure and the shared deployment document contract.

Example source files: [manifest](../examples/dtypes_packages/training_preset/config.yaml),
[preset](../examples/dtypes_packages/training_preset/data/preset.yml),
[examinations](../examples/dtypes_packages/training_preset/data/examinations.yml),
and [optional employees](../examples/dtypes_packages/training_preset/optional/employees.yml).

## 1. The directory contract

```text
an_authoring_root/
└── training_preset/                 # module directory
    ├── config.yaml                 # required exact discovery filename
    ├── data/
    │   ├── preset.yml               # centers, genders, labels
    │   └── examinations.yml         # ordinary clinical KB record format
    └── optional/
        └── employees.yml           # excluded unless config selects it
```

Use `.yml` for new data files. **Keep `config.yaml` named exactly this way**:
the normal discovery and ZIP import paths expect it. The module directory,
`config.yaml.name`, and requested registry module identity should match.

The manifest is a YAML **mapping**. Each selected data file is a YAML **list
of records**. Records have `model` and their fields at the same level; do not
wrap them in Django fixture `fields:` or use `model: endoreg_db.center`.

Files merely placed next to the manifest are not automatically included. Select
them through `data.files` or `data.dirs`. Directory selection is recursive;
keep unrelated YAML documents outside selected directories. Relative paths are
resolved from the manifest's directory and must remain inside the module.

## 2. The manifest

```{literalinclude} ../examples/dtypes_packages/training_preset/config.yaml
:language: yaml
```

| Field | Contract |
| --- | --- |
| `name` | Required, nonempty module identity. Prefer a stable `snake_case` identifier. |
| `version` | Required, nonempty string. Quote it; use a new version for published changes. |
| `description`, `author`, `medical_field` | Optional descriptive metadata. |
| `data.files` | Explicit list of data files relative to the module directory. |
| `data.dirs` | Optional list of directories scanned recursively for `.yaml` and `.yml` data. |
| `modules` | Names of composed modules that the loader must resolve. |
| `depends_on` | Names of prerequisite modules, loaded before dependents. |

Keep `modules` and `depends_on` empty for this standalone example. References
are module **names**, not file paths or invented `name@version` strings. For a
multi-module artifact, include the referenced modules and their manifests in
the resolved source tree. Avoid competing configurations for the same module.
The resolver checks missing dependencies, cycles, and ambiguous configurations;
request the root package with an explicit module/version identity.

## 3. Host presets: centers, genders, and labels

```{literalinclude} ../examples/dtypes_packages/training_preset/data/preset.yml
:language: yaml
```

`study_preset` is backed by `StudyPreset` in
`lx_dtypes.models.knowledge_base.study_preset`. All five collections are optional
and default to empty lists. Nested items do not need a `model` discriminator.

| Collection | Fields used by the host projection | Identity/reference rules |
| --- | --- | --- |
| `centers` | Explicit `name` using the existing ledger `Center` contract | `name` is the host's immutable `center_key`. Use that key for an existing center, not its display name. |
| `genders` | Required `name`; optional `abbreviation`, `description` | Unique natural name. Use the canonical gender names expected by the deployment. |
| `label_types` | Required `name`; optional `description` | Unique natural name. |
| `labels` | Required `name`; optional `label_type`, `description` | `label_type` references a supplied or existing label-type name. |
| `label_sets` | Required `name` and integer `version`; optional `labels`, `description` | Identity is `(name, version)`; `labels` contains supplied or existing label names. |

Use real YAML lists and integers, not comma-separated strings or quoted label-set
versions. Names must be nonempty and at most 255 characters. Duplicate natural
identities are invalid; two label sets may share a name if their versions differ.
Do not populate `centers[].examiners`; use the optional employee record below.

The host preserves existing primary keys. It rejects ambiguous legacy matches
instead of selecting an arbitrary row. The reused ledger models expose more
fields than this host projection persists: UUIDs, tags, contact data, and other
ledger metadata are not a replacement for the explicit host identity rules.

## 4. Examinations use the existing knowledge-base schema

```{literalinclude} ../examples/dtypes_packages/training_preset/data/examinations.yml
:language: yaml
```

An examination is an ordinary `model: examination` record, not a nested field
inside `study_preset`. Its `examination_types`, `findings`, and `indications` are
lists of natural names. The host supports names of at most 100 characters for
examinations and examination types. Reuse existing clinical definitions; the
empty references here make the structural example independently importable.

**Loading a package and provisioning its complete clinical graph are different
operations.** `import_study_preset` creates examination types and examinations,
but referenced findings and indications must already exist in the host database.
It fails and rolls back the whole projection when a reference is missing. It
does not provision every clinical model just because the package contains it.
The wider clinical migration is tracked separately in endoreg-db's
`feature-tracking/DtypesStudyDefinitions.yml`.

## 5. Employees are always optional

```{literalinclude} ../examples/dtypes_packages/training_preset/optional/employees.yml
:language: yaml
```

This is `CenterEmployeeList`, whose nested entries reuse
`lx_dtypes.models.ledger.examiner.Pydantic.Examiner` and `ExaminerDataDict`.

- `center` references the center's immutable host key, exactly matching
  `centers[].name` in this preset or an already provisioned center.
- Supply nonempty `first_name` and `last_name`, each at most 255 characters.
  The literal `unknown` is not a valid recognition name or center reference.
- A supplied `center_employee_list` must contain at least one examiner. To
  provide no employees, omit the record or leave its file unselected.
- Employees may be shipped in terminology packages; they are never required
  for package loading or study-preset import.
- Host projection adds names to recognition lists. It neither deletes local
  names nor creates clinical examiner identities from this document.
- Without stored center-specific names, the report reader leaves overrides
  unset and lx-anonymizer uses its own configuration. Package validity alone
  does not establish anonymization quality.

To enable the example, uncomment `optional/employees.yml` in `data.files`.
Use neutral package/record identifiers rather than embedding employee names in
those identifiers. Do not include patient records or secrets in presets.

## 6. Validate before registration or database import

From an lx-data-models checkout with its development environment activated,
lint the clinical data file:

```sh
python scripts/lint_kb_yaml.py docs/examples/dtypes_packages/training_preset/data/examinations.yml
```

The current standalone linter's model allowlist does not yet include
`study_preset` and `center_employee_list`; linting the entire example manifest
reports `unknown_model`. These records are supported by the normal package
loader. Do not rename or discard them to satisfy that older allowlist.

Load the exact identity through the real resolver to validate the whole package.
This reads and validates
the package without provisioning database rows:

```sh
python - <<'PY'
from pathlib import Path
from lx_dtypes.models.interface.KnowledgeBaseResolver import load_knowledge_base

kb = load_knowledge_base(
    "training_preset",
    version="1.0.0",
    input_dirs=[Path("docs/examples/dtypes_packages").resolve()],
)
assert kb.config.name == "training_preset"
assert kb.config.version == "1.0.0"
assert "training_setup" in kb.study_preset
assert "training_examination" in kb.examination
print("Package valid; employee lists:", len(kb.center_employee_list))
PY
```

Expected employee count is `0` with the checked-in manifest, or `1` after
explicitly selecting the optional file. YAML linting alone is insufficient:
resolver validation and host reference checks cover different contracts.

For field-level schema inspection, the owning Pydantic classes expose
`model_json_schema()`: `KnowledgeBaseConfig`, `StudyPreset`,
`CenterEmployeeList`, and the existing clinical knowledge-base models. Reuse
these contracts in tooling instead of implementing another YAML schema.

## 7. Register, then project into endoreg-db

In lx-annotate/endoreg-db, the shared runtime directory is
`get_runtime_paths().terminology`, exposed as `TERMINOLOGY_ROOT`. Other callers
may provide their own service and registry as shown above. Each registry maps
an exact module and version to package locations. A package manifest must not
hardcode any of those installation paths.

Use the existing LX-Annotate terminology upload workflow for normal deployment.
A ZIP must contain `config.yaml` at its root, or a single outer module directory
containing it, plus every selected data file and required module. For this
example, ZIP the `training_preset/` directory, not the entire examples parent.
An already registered module/version is rejected by the upload service. The
current `TerminologyService.import_zip` registers the package; selecting it as
active is a separate operation. Do not infer activation from upload success.

For a local authoring registry, the existing CLI accepts:

```sh
lx-dtypes-kb-registry register-local ./kb_registry.json \
  --module training_preset --version 1.0.0 \
  --input-dir "$(pwd)/docs/examples/dtypes_packages"
```

That creates a **local authoring registry**, not the host's shared registry.
It does not copy the package. Keep its source tree available. When working with
an existing deployed registry, use its governed import workflow rather than
overwriting its JSON. Do not confuse `LX_DTYPES_KB_REGISTRY` used by standalone
resolution with the host `TerminologyService` rooted at `TERMINOLOGY_ROOT`.

Once the exact package is registered in the host's shared terminology storage,
run these from the configured Django host (with database migrations applied):

```sh
python manage.py import_study_preset --module training_preset --module-version 1.0.0
```

To add only optional names to centers that already exist:

```sh
python manage.py import_center_employees --module training_preset --module-version 1.0.0
```

The second command succeeds with zero employee lists when none are selected.
It does not create centers. The first command can provision centers from the
preset before adding optional names. Both use explicit package identities;
neither selects an active study. The host option is `--module-version` because
Django reserves `--version` for its own version output.

## Deployment setup v1

The frozen v1 field contract is `DeploymentSetup` in
`lx_dtypes.models.contracts.deployment_setup`. A deployment document is a YAML
mapping with `schema_version: '1.0'`. All keys use `snake_case`; unknown fields
and unsupported schema versions are errors.

| Field | Contract |
| --- | --- |
| `schema_version` | The quoted literal `'1.0'`. |
| `site.center_key` | Required immutable host center identity, 1–255 characters: lowercase letters, digits, underscores and hyphens, beginning with a letter or digit. |
| `site.name` | Required display name, 1–255 characters with no surrounding whitespace. |
| `reference_packages` | Optional list, default empty; each selection has exact `module` and `version`, and optionally `content_sha256`. The host projects the resolved reference catalogue closure. |
| `study_packages` | Optional list, default empty; the same identity/digest fields plus `activate`, default `false`. The host resolves definitions and can explicitly select one active registry knowledge base. |
| `content_sha256` | Optional 64-character lowercase hexadecimal digest of the complete resolved source dependency closure. Use the digest produced by planning, not a hash of this setup file. |
| `adopt_existing` | Boolean, default `false`. Explicitly allow equivalent legacy reference rows to be adopted with preserved primary keys; never overwrite conflicting content. |

Versions are exact strings, not range selectors. Each package role can select a
module only once. The same module may appear in both roles only with matching
version and digest pins. Conflicting selections and more than one
`activate: true` are invalid.
Unknown selections fail; a missing package is never replaced by a default.
When a digest is omitted, planning resolves it into the reviewed lock artifact.
Applying requires a matching lock and checks content again.

The host command exports templates directly from `lx_dtypes/setup_templates/`:
`minimal`, `coloreg`, `training`, and `green_endoscopy`. Export one rather than
copying a second maintained schema example:

```sh
python manage.py setup_deployment template coloreg --output setup.yml
python manage.py setup_deployment schema --output deployment_setup.schema.json
```

The generated JSON Schema is the editor contract. The runtime Pydantic model
also checks invariants that require validation across fields; registry and host
checks happen after schema validation. To change the site's identity, edit the
template before first import and preserve the chosen key thereafter.

`activate: false` means leave the current active selection unchanged. Activation
is registry knowledge-base selection, not clinical approval, dataset creation,
patient access, or provisioning all graph and preset records. Employees remain
separate and optional. Additional local clinical definitions require a governed
versioned package; the setup document cannot override package fields inline,
choose arbitrary filesystem/network sources, or execute code.

Run `setup_deployment validate`, then `plan`, review its generated lock, and use
`apply` as documented in the host guide. Package registration, database migrations
and registry provisioning remain explicit operations. A change to this frozen
document contract requires a schema-version decision and coordinated host
support; do not silently reinterpret existing v1 fields.

## Complete reference catalogues

`reference_catalog` is a standard knowledge-base record for typed relational
reference definitions. It uses `ReferenceCatalogPayload` and a discriminated
`ReferenceRecord` union. The `record_type` selects an explicit shared contract;
it never names an arbitrary Django model or executable import. All fields use
snake_case, unknown fields fail validation, references use semantic names and
versioned label sets use both name and integer version.

```yaml
- model: reference_catalog
  name: contraindications
  payload:
    schema_version: '1.0'
    records:
      - record_type: contraindication
        name: declared_contraindication
        description: 'An explicitly authored contraindication definition.'
```

A complete executable package is shipped at `lx_dtypes/data/terminology/endoreg_reference`.
Its `config.yaml` explicitly selects 50 `.yml` files. It preserves the previous
EndoReg bootstrap catalogue as `endoreg_reference@1.0.0`, including clinical
categories that do not fit the existing findings graph: diseases, medications,
laboratory definitions and examination times. Operational records have explicit
types too; patient records, employee names, model weights and active-model
selection are outside this contract.

Optional packages use the same format:

- `endoreg_workforce@1.0.0`: 39 profession, qualification and shift reference
  definitions across five `.yml` files; no employees or assignments.
- `endoreg_green_endoscopy@1.0.0`: 153 sustainability definitions across twelve
  `.yml` files, with shared units and centers from `endoreg_reference`.

Unnamed center/resource, center/waste, product/material and product/weight records
use explicitly declared composite natural keys. Quantities are content, not
identity. Never invent a synthetic `name` for a host table without that field.
The finite-number contract uses null for missing legacy product weights; it
rejects infinity and NaN in authored packages.

`coloreg@0.2.0` adds `endoreg_reference` to its standard dependency closure while
retaining the original `coloreg@0.1.0` resources. Resolved catalogues can be
exported through `KnowledgeBase.export_record_lists()["reference_catalogs"]`.
Before projection, `ReferenceCatalogSnapshot` validates the complete dependency
closure and its content digest. Duplicate identities, duplicate links and
unresolved relationships are errors. Dates and times retain their native types.

Host projection is deliberately separate from core graph projection. Historical
catalogue meanings are preserved even where newer canonical graph definitions
use the same names differently. The host refuses incompatible reuse; selecting
a newer package cannot silently rewrite an existing patient-linked definition.
See the endoreg-db dataloader guide for dry-run reconciliation, explicit legacy
adoption, projection selection and transaction semantics. New identities or
clinical changes require new package versions; changing bytes under an imported
identity is rejected.

## 8. Agent and reviewer checklist

1. Read this guide, the owning Pydantic contracts, and the intended host importer
   before generating package content. Do not guess accepted fields from model names.
2. Reuse canonical clinical names and existing ledger contracts. Keep all keys
   in `snake_case` and keep patient data out of reference packages.
3. Check the exact `config.yaml` filename, quoted package version, selected
   file paths, and module/dependency closure. Never rely on directory ordering
   to choose between incompatible definitions.
4. Check references and identities: center key, natural record names, and
   `(name, version)` for label sets. Confirm the host persists each authored
   field required by the task; successful parsing is not proof of persistence.
5. Treat employees as optional. Do not generate required empty employee records
   or change examiner hashing to accommodate a package.
6. Run lint and exact-identity loading. Verify database import, reimport,
   rollback, and reference resolution in an isolated host environment before
   using new definitions operationally.
7. Record readiness evidence in the feature tracker. Package registration,
   active-package selection, host projection, dataset/cohort setup, and clinical
   approval are separate steps.

## Common mistakes

| Symptom | Check |
| --- | --- |
| Module cannot be discovered | Manifest is `config.yaml`, identity matches, and the registry points to the package directory or containing source tree. |
| Registered package is missing in the application | Inspect `get_terminology_service().registry_path` in the host; the registration may have used a different registry. |
| Package works on one centre only | Check mounted source paths, process read permissions, exact versions, and the complete dependency closure on that centre. |
| Registry rejects an existing identity at another path | Keep the existing source available; use a governed relocation or a new version rather than silently redirecting historical data. |
| A data file has no effect | It is selected by `data.files` or included by `data.dirs`. |
| Unknown model or extra-field error | Use registered model names and flat record fields, not legacy Django fixture syntax. |
| Employee import fails | A referenced center exists or is declared in the preset; names are nonempty and not `unknown`. |
| Label-set import is invalid | Supply an integer `version` and valid label references. |
| Package loads but host import fails | Clinical references may be absent, legacy identities ambiguous, or center keys incompatible. |
| Edited installed files do not appear | Publish/register a new version instead of relying on mutation of cached package content. |

Dataset/cohort YAML using `StudySetupDefinition` is a separate document contract.
Both cohorts and `StudyPreset` can carry validated `study_metadata` for participating
centers, age groups, exact terminology dependencies, and inclusion criteria. See
[the shared metadata contract](study-metadata.yml) for fields and host evaluation
semantics. Metadata does not grant patient access or activate terminology.
Do not put it in a KB data directory or wrap it in `model: study_preset`. Follow
the study-setup section of the authoring guide for that workflow.

For the ColoReg resection study, see the [endpoint and linkage specification](coloreg-resection-study.yml).
Its [study document](../../lx_dtypes/data/study_metadata/coloreg_resection.yml) uses
`StudySetupDefinition`; lesion-size filtering and longitudinal analysis remain
explicit host operations.
