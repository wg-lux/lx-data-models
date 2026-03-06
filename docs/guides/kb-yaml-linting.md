# KB YAML Linting

Use the lint command to help authors produce parseable, consistent concept YAML files with explicit line references.

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
- invalid root/item structure
- duplicate `(model, name)` definitions (with both source locations)
- deprecated model aliases (for example `finding_validator` instead of `findings_validator`)
- mixed finding reference styles in `report_template_section.findings`

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
