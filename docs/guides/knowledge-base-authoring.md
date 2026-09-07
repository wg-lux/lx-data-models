# Knowledge-Base Authoring

This guide is the recommended path for authoring and publishing `lx-dtypes`
knowledge-base modules in this monorepo.

It ties together three parts of the workflow:

1. author the YAML bundle with `lx-terminology-editor`
2. lint and review the generated module in `lx-data-models`
3. publish the module as a Nix-packaged knowledge base and app bundle

## Read This First

Use these documents in this order:

1. `lx-terminology-editor/README.md`
2. `docs/guides/knowledge-base-authoring.md`
3. `docs/guides/kb-yaml-linting.md`

## Core Terms

- knowledge base: a versioned collection of YAML modules that `lx-dtypes` can load
- module: one publishable folder containing `config.yaml` plus one or more data files
- registry: a JSON file mapping `module -> version` to typed `provider` or
  `filesystem` source descriptors
- authoring bundle: the editable YAML structure produced by `lx-terminology-editor`
- packaged kb: the Nix derivation that installs a module and emits a registry JSON
- app bundle: the Python package plus packaged KB, wrapped with `LX_DTYPES_KB_REGISTRY`

When `LX_DTYPES_KB_REGISTRY` is configured, runtime resolution is fail-closed:
callers must request an explicit `module@version`, and that exact identity must
exist in the registry. The resolver validates the selected artifact's root
`config.yaml` against the requested identity and never substitutes another
registered version, checkout, or example data. A registered provider may
resolve an immutable resource from the installed wheel, while explicit
`input_dirs` remain available for authoring, imports, and deployment-owned
filesystem artifacts.

Every referenced `modules` and `depends_on` entry is resolved transitively from
the selected artifact before it is accepted. Missing dependencies, conflicting
versions, and ambiguous root `config.yaml` candidates are typed load errors;
input-directory ordering is not a package-selection mechanism.

Filesystem-source `input_dirs` may also contain an HTTPS GitHub tree URL ending in the
module directory, for example:

```json
{
  "modules": {
    "star_upper_gi": {
      "0.1.1": {
        "sources": [{
          "kind": "filesystem",
          "input_dirs": [
            "https://github.com/wg-lux/lx-data-models/tree/main/lx_dtypes/data/star_upper_gi"
          ]
        }]
      }
    }
  }
}
```

`lx-dtypes` downloads the repository archive into
`LX_DTYPES_REMOTE_CACHE_ROOT` (or the user cache directory), validates the
archive paths and size, and passes the materialized parent directory to the
existing YAML loader. Cache writes use the audited `endoreg_db` filesystem
adapter supplied by the `lx-annotate` host. Only HTTPS `github.com` tree URLs
are accepted. For reproducible deployments, use a commit SHA as the tree ref
rather than a mutable branch name.

## Storage Topology and Runtime Resolution

`lx-dtypes` separates:

- **Registry storage (`registry.json`)**: which module/version identities map to
  stable provider identities or deployment-owned physical roots.
- **Module internals (`config.yaml` + `data/*`)**: what each KB version contains.

Built-in wheel content is registered by provider and digest. The runtime
resolves its installation path; do not persist a resolved `site-packages`,
virtual-environment, or Nix-store wheel path:

```json
{
  "modules": {
    "star_upper_gi": {
      "0.1.1": {
        "sources": [{
          "kind": "provider",
          "provider": "lx_dtypes.builtin",
          "content_sha256": "<64-character catalog digest>"
        }]
      }
    }
  },
  "active": {
    "module_name": "star_upper_gi",
    "version": "0.1.1"
  }
}
```

### Startup bootstrap and migration

- Before Django starts, the deployment runs `lx-dtypes-kb-registry bootstrap`.
- The CLI requires `--registry` or `LX_DTYPES_KB_REGISTRY` and fails closed when
  neither is configured.
- If the configured registry file is missing, empty, or has no active selection,
  bootstrap registers packaged provider descriptors and activates the
  configured/default packaged identity.
- Every package-catalog identity is fully loaded during bootstrap.
- A stale active built-in provider or legacy installed-wheel filesystem entry
  is atomically migrated to the matching current catalog identity.
- Active custom/imported filesystem identities are preserved. Resolution never
  silently chooses the first registered module or another version.
- Django application import performs no implicit registry mutation; deployment
  ordering and bootstrap failures remain visible to the service manager.

For example:

```bash
export LX_DTYPES_KB_REGISTRY=/var/lib/my-host/terminology/registry.json
lx-dtypes-kb-registry bootstrap --module star_upper_gi
python -m django migrate --noinput
```

### Import flow: from KB ZIP upload to `config.yaml`

The backend import endpoint is `POST /terminology/bundles/import`.

1. The API parses the ZIP (`_read_zip_file_map`) and normalizes a single-root ZIP
   layout.
2. It reads root `config.yaml` (`_read_bundle_identity`) to get
   `module_name`, `version`, and optional `medical_field`.
3. It resolves an import destination:
   - `LX_DTYPES_TERMINOLOGY_IMPORT_ROOT` if set, otherwise
     `<registry parent>/terminology-packages`.
4. Files are written to
   `<import root>/<module>/<version>/.tmp/<module>-<uuid>/...`, then atomically
   moved to `<import root>/<module>/<version>`.
5. `_register_imported_bundle()` stores a typed `filesystem` source containing
   the absolute `input_dirs` path for that version and marks it active when
   imported through the endpoint.

Because paths are now registry-driven, moving a KB version directory changes only
registry state; `config.yaml` remains stable and local.

### `config.yaml` path normalization model

`DataLoader` discovers `config.yaml` from the resolved `input_dirs`, loads each
candidate, then calls `KnowledgeBaseConfig.normalize_data_paths(config_file)`.

- `data.dirs` and `data.files` are always resolved against
  `config_file.parent`.
- Internal paths therefore stay portable across absolute moves of the KB directory.

In practice this means `registry.json` is the location layer, while `config.yaml`
is the composition layer.

## Recommended Workflow

### 1. Author the Bundle in `lx-terminology-editor`

From the monorepo root:

```bash
cd lx-terminology-editor
direnv allow
devenv shell
python server.py
```

Then open `http://localhost:4173`.

The editor is the preferred authoring surface for terminology content. It can:

- edit bundle metadata and terminology modules
- generate `config.yaml` plus `data/*.yaml`
- run the browser-packaged `lx-data-models` KB linter through **Paket prüfen**
- export the complete bundle through **ZIP zur Veröffentlichung herunterladen**

The editor is a static browser application. It does not write a `.published/`
directory, update `kb_registry.json`, or activate runtime terminology. The ZIP is
the authoring handoff artifact.

### 2. Publish Through LX-Annotate

Import the exported ZIP in the LX-Annotate reporting or terminology settings UI.
The frontend submits each ZIP sequentially as multipart field `file` to:

```text
POST /dtypes-api/terminology/bundles/import
```

The server strips the editor ZIP's single outer directory, reads the root
`config.yaml`, validates the full module graph, installs the artifact, writes a
filesystem source to the governed registry, and activates the imported identity.
An existing module/version is rejected instead of overwritten.

The successful identity is immediately addressable through the stable graph API:

```text
GET /dtypes-api/knowledge-bases/{module}/{version}/graph
GET /dtypes-api/knowledge-bases/{module}/{version}/examinations/{name}/reporting-context
```

Those routes and the `knowledge_base_graph_v1` response contract are the
integration boundary used by the LX-Annotate reporting frontend.

For a local CLI-only prototype, extract the ZIP so its package directory sits
under one data root, register that root, and smoke-test the exact identity:

```bash
lx-dtypes-kb-registry add ./kb_registry.json \
  --module my_module \
  --version 1.0.0 \
  --input-dir /path/to/extracted-parent
export LX_DTYPES_KB_REGISTRY="$PWD/kb_registry.json"
lx-dtypes-prototype-kb-smoke --module my_module --version 1.0.0
```

This keeps both supported handoffs deterministic because:

- the editor remains the single authoring surface
- `lx_dtypes` resolves the module through the normal versioned registry path
- the requested module and version are explicit and deterministic

### 3. Package an Approved Module in `lx-data-models`

Once the bundle is approved, extract and copy the module into the module source
tree used by `lx-data-models`.

The current Nix example package in `package.nix` packages:

```text
lx_dtypes/data/star_upper_gi/
```

That means the module folder name is currently part of the packaging contract.

Important naming rule:

- the module folder name is the source of truth for the packaged module name

In the current package definition:

- `kbSource = ./lx_dtypes/data/star_upper_gi;`
- `kbModuleName = builtins.baseNameOf (toString kbSource);`
- the Nix package name is derived from that folder name

If you change the published module name, update the packaged source folder to match.

### 4. Lint the YAML Before Packaging

Run the KB linter against the module config or data directory:

```bash
python scripts/lint_kb_yaml.py --config lx_dtypes/data/star_upper_gi/config.yaml
```

or:

```bash
python scripts/lint_kb_yaml.py lx_dtypes/data/star_upper_gi
```

Use strict mode when you want authoring governance checks as part of CI:

```bash
python scripts/lint_kb_yaml.py \
  --config lx_dtypes/data/star_upper_gi/config.yaml \
  --strict-aliases \
  --strict-mixed-styles \
  --fail-on-warnings
```

See `docs/guides/kb-yaml-linting.md` for the full linting behavior.

### 5. Package the KB with Nix

`lx-data-models` exposes three Nix outputs:

- Python package: `packages.lx-dtypes`
- packaged knowledge base: `packages.star-endoscopy-kb`
- deployable app bundle: `packages.lx-dtypes-app`

The current flake wiring lives in:

- `flake.nix`
- `package.nix`
- `app-package.nix`
- `devenv.nix`

Useful commands:

```bash
nix build .#star-endoscopy-kb
nix build .#lx-dtypes-app
devenv eval outputs
```

`devenv eval outputs` is the most reliable way to inspect the current split
outputs when `devenv build` shows cached summaries.

## What Nix Publication Produces

The KB derivation installs two things:

- the module payload under `$out/share/lx-dtypes/knowledge-bases/<module-name>/`
- a registry file under `$out/share/lx-dtypes/registries/<module-name>.json`

The registry looks like this:

```json
{
  "modules": {
    "star_upper_gi": {
      "0.1.0": {
        "input_dirs": [
          "/nix/store/.../share/lx-dtypes/knowledge-bases"
        ]
      }
    }
  }
}
```

That is the handoff point between authoring and consumption: downstream tools do
not need to know your authoring workspace, only the packaged registry path.

## App Bundle vs Standalone KB

Use the standalone KB when another process already has the Python package and
only needs the terminology module plus registry.

Use the app bundle when you want one deployable output containing:

- the `lx-dtypes` Python package
- the packaged knowledge base
- wrapped CLIs with `LX_DTYPES_KB_REGISTRY` pointing at the bundled registry

That wrapping happens in `app-package.nix`.

## Testing the Published Module

The repository includes a Nix test for packaged module resolution in
`tests/nix/module_resolution_test.nix`.

Run:

```bash
nix run .#nixtests
```

This verifies that:

- the packaged registry JSON is installed
- the registry resolves the packaged module root
- the app bundle ships the bundled KB registry

## Practical Authoring Rules

- Prefer editing module content through `lx-terminology-editor`.
- Keep the module folder name stable and intentional, because the current Nix package derives its module identity from that folder.
- Lint before packaging.
- Treat the editor ZIP as an authoring handoff, not as an active runtime artifact.
- Treat the registry entry written by the validated LX-Annotate import as the deployed filesystem handoff.
- Treat the Nix-installed registry JSON as the deployable handoff artifact.

## Reproduce and maintain versioned numeric classifications

Owner: **lx_dtypes maintainers**. This section is the canonical workflow for
the classification-versioning demonstration and publication reconciliation.
The machine-readable [reconciliation inventory](../data-reconciliation.yml)
records the compared PR commit, exact MST prefix hashes, counts, and STAR repairs.
It is an artifact inventory, not a production-readiness assessment.

### Run the example

From the repository root, after installing the development environment:

```bash
export LX_DTYPES_KB_REGISTRY="$PWD/temp/generated_exports/classification_versioning/registry.json"
uv run python -m lx_dtypes.scripts.kb_registry bootstrap
uv run python -m lx_dtypes.models.interface.examples.demo_classification_versioning \
  --measurements demo-data/classification_versioning/measurements.yml
```

Bootstrap provisions all catalog versions into this separate demo registry. It
does not select a new classification scheme for existing patient records.
An active release that is still in the catalog is preserved, including a
nondefault historical release. Missing versions fail explicitly.

The example verifies expected results before writing
`temp/generated_exports/classification_versioning/table4.csv` and `results.yml`.
The CSV compares the five synthetic measurements 4, 6, 8, 15 and 22 mm. The YAML
contains ten interpretations with the complete source measurement, source KB
identity, interpretation KB identity, classification, choice and rule digest.
Repeating the command produces the same result content. Use `--output-dir` to
choose another generated-output location; use `--help` for arguments.

### Understand the boundaries

```text
NumericMeasurement: original value + unit + descriptor + source identity
       │
       ├── polyp_size_category@1.0.0 → derived choice + rule digest
       └── polyp_size_category@2.0.0 → derived choice + rule digest
```

Both releases declare `name: polyp_size_category`. A directory label does not
define clinical identity. `load_numeric_classification()` uses the existing
registry/resolver and `DataLoader` to load the exact identity, then validates
the associated `numeric_rules.yml` against its classification choices and unit.
The two knowledge bases remain separate because their names overlap. Do not
import them into one collection or overwrite an examination's original KB
identity when computing a later interpretation.

Version 1 is an **illustrative binary comparator**, not a historical ESGE release.
Version 2 implements whole-number size groups described in the
[ESGE 2024 guideline](https://www.esge.com/assets/downloads/pdfs/guidelines/2024_a-2304-3219.pdf).
It computes size groups only. Treatment depends on additional clinical context;
an upper-GI measurement is not evidence that a colorectal treatment rule applies.
The 8 mm polyp in the existing STAR ledger is used in the preservation test.
The existing 6 mm ledger finding is a diverticulum; Table 4 uses a separate,
explicitly synthetic five-measurement fixture.

| Input | 1.0.0 | 2.0.0 |
|---|---|---|
| 5 mm | `size_le_5` | `size_le_5` |
| 6 or 9 mm | `size_gt_5` | `size_6_9` |
| 10 or 19 mm | `size_gt_5` | `size_10_19` |
| 20 mm | `size_gt_5` | `size_ge_20` |
| 5.5 mm | `size_gt_5` | rejected; whole numbers required |
| zero, negative, nonfinite, boolean or string input | rejected | rejected |

No implicit rounding, unit conversion or guessing is performed. A future
continuous interpretation must publish its fractional policy explicitly under
a new version; do not silently fill gaps between integer guideline labels.

### Author a release in YAML

The current/default bundle is `lx_dtypes/data/polyp_size_category/`. Its historical
release lives at
`lx_dtypes/data/versions/polyp_size_category/1.0.0/polyp_size_category/`.
Each release has these files:

| File | Purpose |
|---|---|
| `config.yaml` | Stable logical name, release version and data file selection |
| `data.yml` | Canonical classification, permitted choices and unit |
| `numeric_rules.yml` | Strict executable numeric partition bound to that release |

Keep the discovery filename `config.yaml`. Data payloads support both `.yaml`
and `.yml`; files referenced both explicitly and through a directory are loaded
once. The rules sidecar is **not** a KB record list, so do not include it in
`data.files` or put it inside a directory selected by `data.dirs`.

An excerpt from the legacy rules is:

```yaml
schema_version: 1
knowledge_base:
  knowledge_base_module: polyp_size_category
  knowledge_base_version: 1.0.0
classification: polyp_size_category
input_descriptor: length_mm_descriptor
unit: millimeter
resolution: continuous
source: Illustrative binary comparator; not a historical guideline release.
rules:
  - choice: size_le_5
    lower: 0.0
    upper: 5.0
    lower_inclusive: false
    upper_inclusive: true
  - choice: size_gt_5
    lower: 5.0
    upper: null
    lower_inclusive: false
    upper_inclusive: false
```

The strict schema rejects unknown fields, duplicate mapping keys, nonfinite
bounds, duplicate choices, empty/reversed intervals, gaps and overlaps. Rules
are ordered and cover a domain from a finite lower bound to infinity; the last
upper bound must be `null`. Every shared endpoint belongs to exactly one rule.
This first schema intentionally does not represent multidimensional clinical
decision rules or domains with an upper limit.

For a new release:

1. Preserve the previous bundle bytes and its dependencies. Copy into a separate
   release root, retain the module name, and change `version` in both config and
   rules. Use new choice names when their meanings change; preserve names for
   unchanged meanings.
2. Edit the clinical definitions and rule boundaries together. Keep citations
   and applicability precise. Update the synthetic expected-result fixture when
   intentionally extending the comparison.
3. Register the new artifact for authoring using `kb-registry add` with an
   `--input-dir` scoped to that release root. Broad roots containing several
   versions of the same module are not a version-selection mechanism.
4. Before packaging, add a distinct `(module_name, version)` entry to
   `lx_dtypes/data/catalog.json`. Exactly one release per logical module has
   `default: true`. Compute `content_sha256` using
   `lx_dtypes.knowledge_bases.knowledge_base_content_sha256(Path(resource_root))`
   with the actual local bundle directory. The digest includes YAML paths and
   bytes, including the rules sidecar and dependencies nested inside the bundle.
   Preserve historical catalog entries; never change their bytes in place.
5. Bootstrap a separate test registry, run the example and the checks below,
   and review the clinical changes independently of structural validity.

The source STAR snapshot uses the supported opaque version string
`0.1.1.post1` to identify a repair of the old demo; the resolver compares exact
strings and does not sort releases. It includes scoped `lx_units@0.1.0.post1`.
Its digest covers those nested unit files. The existing operational STAR
`0.1.2` remains the default.

### Validate before publication

```bash
uv run python scripts/lint_kb_yaml.py --config lx_dtypes/data/polyp_size_category/config.yaml
uv run pytest tests/unit/lx_dtypes/models/interface/test_classification_versioning.py \
  tests/unit/lx_dtypes/models/interface/test_mst_3_0.py \
  tests/unit/lx_dtypes/test_knowledge_base_registry_bootstrap.py -q
uv run pyright
uv run pytest -q
uv run make -C docs html
uv run make -C docs linkcheck
```

The KB linter checks the selected concept files. The versioning tests separately
validate the rules sidecar, real ledger preservation, boundaries, identity
mismatches, unavailable versions and strict inputs. MST reconciliation verifies
the PR additions byte-for-byte against the existing source prefixes and validates
the full core graph. These checks establish software consistency, not a complete
independent audit against every clinical source table.

### Reconcile the manuscript

The historical `demo-data/star_upper_gi` is retained unchanged as evidence; new
examples should resolve a catalog artifact. Its 22 findings, 21 classifications
and 71 choices contain dangling references. The repaired release retains the
findings and classifications, adds the eight referenced mucosal choices, fixes
two descriptor references and corrects the scoped millimeter unit. It therefore
has **79 choices**, three descriptors and 41 units. Do not describe the original
71-choice artifact as having passed full referential validation.

The repaired snapshot retains 22 authoring-lint warnings for missing finding
descriptions inherited from the demo. It is a reproducibility artifact, not an
updated clinical reporting interface. These warnings do not affect core-reference
validation or the numeric comparison; the operational STAR default remains 0.1.2.

The two MST files in PR #32 are already present in this checkout. The complete
`mst_3_0@3.0.0` has 357 findings, 39 classifications, 285 choices, 142 indications,
40 interventions and 12 examinations. The draft's larger counts must not be
reproduced by inventing additional concepts. In the
[WEO source](https://www.worldendo.org/assets-craft/pdf/resources/mst-3-0.pdf),
§7.3 on page 41 lists actions and outcomes; it does not contain the five-level
severity table attributed to it in the draft. A separately sourced severity
scheme would need its own provenance and explicit extension identity.

The [editorial replacement specification](../manuscript-reconciliation.yml)
and `scripts/revise_lxdm_manuscript.py` produce a separate revised DOCX with an
audit of replacements. They never overwrite the original. Follow the command
in that YAML file; review the resulting document before submitting it.

## Related Guides

- KB linting details: `docs/guides/kb-yaml-linting.md`
- Terminology editor workflow: `lx-terminology-editor/README.md`
- Monorepo overview of local publication: `/home/admin/endoreg-db/README.md`
