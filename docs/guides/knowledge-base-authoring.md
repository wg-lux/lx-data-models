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

- At Django app startup `LxDtypesDjangoConfig.ready()` calls
  `ensure_default_terminology_registry()`.
- If `LX_DTYPES_KB_REGISTRY` is not configured, the seeding step writes nothing.
- If the configured registry file is missing, empty, or has no active selection,
  bootstrap registers packaged provider descriptors and activates the
  configured/default packaged identity.
- Every package-catalog identity is fully loaded during bootstrap.
- A stale active built-in provider or legacy installed-wheel filesystem entry
  is atomically migrated to the matching current catalog identity.
- Active custom/imported filesystem identities are preserved. Resolution never
  silently chooses the first registered module or another version.

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

## Related Guides

- KB linting details: `docs/guides/kb-yaml-linting.md`
- Terminology editor workflow: `lx-terminology-editor/README.md`
- Monorepo overview of local publication: `/home/admin/endoreg-db/README.md`
