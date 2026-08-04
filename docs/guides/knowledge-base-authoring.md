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
- registry: a JSON file mapping `module -> version -> input_dirs`
- authoring bundle: the editable YAML structure produced by `lx-terminology-editor`
- packaged kb: the Nix derivation that installs a module and emits a registry JSON
- app bundle: the Python package plus packaged KB, wrapped with `LX_DTYPES_KB_REGISTRY`

When `LX_DTYPES_KB_REGISTRY` is configured, runtime resolution is fail-closed:
callers must request an explicit `module@version`, and that exact identity must
exist in the registry. The resolver validates the selected artifact's root
`config.yaml` against the requested identity and never falls back to checkout,
wheel, or example data. Explicit `input_dirs` remain available only for direct
authoring/import validation before an artifact is registered.

Every referenced `modules` and `depends_on` entry is resolved transitively from
the selected artifact before it is accepted. Missing dependencies, conflicting
versions, and ambiguous root `config.yaml` candidates are typed load errors;
input-directory ordering is not a package-selection mechanism.

Registry `input_dirs` may also contain an HTTPS GitHub tree URL ending in the
module directory, for example:

```json
{
  "modules": {
    "star_upper_gi": {
      "0.1.1": {
        "input_dirs": [
          "https://github.com/wg-lux/lx-data-models/tree/main/demo-data/star_upper_gi"
        ]
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
- run the `lx-data-models` KB linter through the local `ok` button
- publish the current bundle under `.published/<publish-name>/<version>/`
- update `.published/kb_registry.json`

That local registry is already in the format expected by `LX_DTYPES_KB_REGISTRY`.

For deterministic prototyping in `lx-data-models`, prefer consuming that
published registry directly instead of copying the bundle into `lx_dtypes/data`
during early iteration.

Inside `lx-data-models/devenv`:

- `LX_DTYPES_EDITOR_KB_REGISTRY` points at `../lx-terminology-editor/.published/kb_registry.json`
- `use_editor_kb` exports `LX_DTYPES_KB_REGISTRY` for the current shell
- `use_packaged_kb` returns to packaged/default resolution
- `lx-dtypes-prototype-kb-smoke --module <name> --version <version>` verifies that an explicit module/version resolves and loads

### 2. Prototype Through The Published Registry

Use the editor-published registry as the first-class prototype handoff:

```bash
cd lx-data-models
devenv shell
use_editor_kb
lx-dtypes-prototype-kb-smoke --module my_module --version 0.1.0-dev.1
```

This is the recommended quick-feedback loop because:

- the editor remains the single authoring surface
- `lx_dtypes` resolves the module through the normal versioned registry path
- the requested module and version are explicit and deterministic

### 3. Move the Module into `lx-data-models`

Once the bundle looks correct, copy the published module into the module source
tree used by `lx-data-models`.

The current Nix example package in `package.nix` packages:

```text
demo-data/star_upper_gi/
```

That means the module folder name is currently part of the packaging contract.

Important naming rule:

- the module folder name is the source of truth for the packaged module name

In the current package definition:

- `kbSource = ./demo-data/star_upper_gi;`
- `kbModuleName = builtins.baseNameOf (toString kbSource);`
- the Nix package name is derived from that folder name

If you change the published module name, update the packaged source folder to match.

### 4. Lint the YAML Before Packaging

Run the KB linter against the module config or data directory:

```bash
python scripts/lint_kb_yaml.py --config demo-data/star_upper_gi/config.yaml
```

or:

```bash
python scripts/lint_kb_yaml.py demo-data/star_upper_gi
```

Use strict mode when you want authoring governance checks as part of CI:

```bash
python scripts/lint_kb_yaml.py \
  --config demo-data/star_upper_gi/config.yaml \
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
- Treat the local `.published/kb_registry.json` from `lx-terminology-editor` as the pre-Nix handoff artifact and prototype source of truth.
- Treat the Nix-installed registry JSON as the deployable handoff artifact.

## Related Guides

- KB linting details: `docs/guides/kb-yaml-linting.md`
- Terminology editor workflow: `lx-terminology-editor/README.md`
- Monorepo overview of local publication: `/home/admin/endoreg-db/README.md`
