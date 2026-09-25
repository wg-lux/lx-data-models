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

## Engineering rules

- Prefer strict Pydantic models, explicit types, and validation at external
  boundaries. Avoid `Any`, silent fallback, and unvalidated dictionaries.
- Preserve stable public package imports and document intentional breaking changes.
- Keep fixtures deterministic and free of patient data, secrets, and local paths.
- Documentation language is English unless a domain-specific German reference is
  explicitly required.
- Generated Sphinx output belongs in `docs/_build/` and must not be committed.

## Verification

Run the narrowest applicable checks from the repository root:

```bash
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
