# KB YAML Linting

Use the lint command to help authors produce parseable, consistent concept YAML files with explicit line references.

Recommended reading order:

1. `docs/guides/knowledge-base-authoring.md`
2. `docs/guides/kb-yaml-linting.md`

## Command

```bash
python scripts/lint_kb_yaml.py --config lx_dtypes/data/report_template_examples/config.yaml
```

You can also lint files/directories directly:

```bash
python scripts/lint_kb_yaml.py lx_dtypes/data/report_template_examples/data
```

## What It Checks

- invalid YAML syntax (`file:line:column`)
- duplicate YAML mapping keys, including nested mappings
- invalid root/item structure
- duplicate `(model, name)` definitions (with both source locations)
- deprecated model aliases (for example `finding_validator` instead of `findings_validator`)
- mixed finding reference styles in `report_template_section.findings`
- unresolved descriptor-unit references across the discovered module graph
- numeric descriptors that would implicitly use the `unknown` unit sentinel
- module references that use an aggregator directory instead of its declared name

The aggregator-name warning is emitted when a consumer references an aggregator
by its folder name even though module loading uses the different `name` declared
in `config.yaml`. Use `--fail-on-warnings` when packaging or import workflows
must resolve every configured module reference.

## Strict Modes

```bash
python scripts/lint_kb_yaml.py \
  --config lx_dtypes/data/report_template_examples/config.yaml \
  --strict-aliases \
  --strict-mixed-styles \
  --fail-on-warnings
```

## CI Recommendation

- Run this command in CI before loading KB modules.
- Keep `pytest` for contract/runtime behavior tests.
- Use linting for authoring feedback and governance checks.

## Related Guides

- Authoring and publication workflow: `docs/guides/knowledge-base-authoring.md`
