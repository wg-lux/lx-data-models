# Hierarchical agent context

Owner: lx_dtypes maintainers. This is the canonical guide to repository context
manifests and their validation; domain guides retain ownership of their contracts.

Start at `../structure.yml`, then follow only the `submodules` needed for the task.
The root links the library, documentation, tests, repository scripts, and demo
data. The library links its model, terminology-service, Django, and packaged-data
domains. Small utility modules stay at the library tier; repository scaffolding
(`features`, `data`, `templates`, `typings`, and environment configuration) stays
at the root tier. Use scoped searches after selecting the owning domain.

The manifests describe architecture. They do not replace `config.yaml`,
`lx_dtypes/data/definitions.yml`, the release catalog, or public Python exports.
In particular, context manifests are placed outside individual KB packages and
their selected record directories so loaders and release digests are unaffected.

## Schema and path conventions

Every manifest has integer `version: 1`, a `tier` (`root`, `domain`, `service`,
`package`, or `tool`), repository-relative `path`, `parent`, `summary`,
`responsibilities`, `boundaries`, `entrypoints`, `dependencies`, `submodules`,
`contracts`, and `tests`. Empty collections are allowed except responsibilities;
text fields must contain non-whitespace text. Custom fields are allowed and must
be preserved when editing. The optional `files` list contains file or directory
paths for locally owned supporting areas that do not need their own manifest.

Only `path` is relative to the repository root. All other paths are relative to
the directory containing the manifest, including `parent`, `entrypoints.file`,
`dependencies.internal`, `submodules.path`, `submodules.manifest`, `contracts.doc`,
`tests.directory`, and each `files` item. Absolute paths and symlink escapes are
rejected. External dependencies are library or protocol names, not file paths.
The root has null parent; each child has exactly one incoming link and points
back to that caller. Child directories must be descendants of their callers.

## Maintenance and verification

When files or architectural boundaries are added, removed, or renamed, update
the owning manifest in the same changeset. Adjust entrypoints and supporting
paths where relevant; these manifests describe architectural tiers, rather than
listing every source file. Add a child only for a substantial domain, service,
or library boundary, and update both sides of its parent link.

Run from the repository root:

```bash
uv run python scripts/lint_structure.py
uv run pytest tests/test_structure.py -q
```

The standalone script uses the existing Pydantic and PyYAML dependencies without
importing application modules. `python scripts/lint_structure.py` also works in
an environment containing those dependencies. It discovers tracked and new,
unignored manifests through `git ls-files`, so a Git checkout is required and
ignored environments, build output, and media trees are never traversed. It
reports schema, missing-reference, parent-link, and root-reachability errors and
exits nonzero on drift. Test commands are documented recommendations; the linter
does not execute them. It does not assess semantic accuracy of prose or record
every file addition, so reviewers must check ownership changes too.

The local pre-commit hook runs this check on every invocation, including the
existing CI quality gate. The standard pytest lane also validates the repository
graph and exercises synthetic failure cases.

## Delegated work

When subagents are explicitly requested, give each one the root manifest and
the manifest chain for its assigned directory tree, the relevant contracts,
and a precise file scope. Keep edits within that tree; coordinate changes to
shared contracts or parent links with the owning agent. Read dependency manifests
only when their interfaces are needed. Delegation does not waive the manifest
maintenance or pre-flight validation requirements in `../AGENTS.md`.
