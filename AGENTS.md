# lx-data-models Agent Guide

This repository owns the reusable `lx_dtypes` package and its typed domain,
knowledge-base, interoperability, and host-integration contracts. Keep package
boundaries explicit and do not move application-specific persistence or service
logic into this repository.

## Before editing

1. Read the relevant guide under `docs/` and inspect existing public imports,
   validators, tests, and downstream contracts.
2. State the exact files in scope and what will remain unchanged.
3. Treat `README.md` as the project entry point and `docs/index.md` as the
   documentation entry point.
4. For cross-repository readiness work, use
   `/home/admin/endoreg-db/feature-tracking/`; do not create Markdown status or
   completion trackers here.

## Authoring terminology packages

Before generating or reviewing package YAML, read
[Structure of a valid lx-dtypes package](docs/guides/dtypes-package-structure.md).
Use its executable documentation example and agent checklist. A standard KB
package, host preset projection, and dataset/cohort setup are separate contracts.

## Engineering rules

- Prefer strict Pydantic models, explicit types, and validation at external
  boundaries. Avoid `Any`, silent fallback, and unvalidated dictionaries.
- Preserve stable public package imports and document intentional breaking changes.
- Keep fixtures deterministic and free of patient data, secrets, and local paths.
- Documentation language is English unless a domain-specific German reference is
  explicitly required.
- Generated Sphinx output belongs in `docs/_build/` and must not be committed.

## Source of Truth & Context Protocol

- Start at [structure.yml](structure.yml) and traverse its `submodules` top-down
  to the domain needed for the task before searching source files. Scope searches
  to that domain rather than broadly grepping the repository, and respect its
  responsibilities, boundaries, public entrypoints, and referenced contracts.
- Context manifests map architecture; existing package configs, resource
  inventories, public exports, and canonical domain guides retain their authority.
- Whenever adding, removing, or renaming files or changing boundaries, update
  the corresponding `structure.yml` files in the same changeset. Preserve custom
  metadata and maintain both child links and parent references. Keep trivial
  folders at their existing architectural tier.
- Before concluding any prompt or submitting a pull request, run
  `uv run python scripts/lint_structure.py` and report any failures or blockers.
- Follow [Hierarchical agent context](docs/agent_context.md) for the schema,
  relative-path conventions, validation, and scoping delegated work.

## Verification

Run the narrowest applicable checks from the repository root:

```bash
uv run python scripts/lint_structure.py
uv run pyright
uv run pytest <test-path-or-node-id> -q
uv run make -C docs html
uv run make -C docs linkcheck
```

For a broad change, run the complete Pyright and pytest lanes after focused tests.
Report what passed, what failed, and any remaining compatibility risk.

## Documentation governance

Cross-repository documentation policy is maintained in
`/home/admin/endoreg-db/quality/documentation_governance.yml` and readiness in
`/home/admin/endoreg-db/feature-tracking/Documentation.yml`. New documentation
must have a clear owner and canonical topic. Merge or replace duplicate guides
instead of allowing multiple pages to claim the same contract.
