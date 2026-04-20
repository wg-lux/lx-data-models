# Report Template Graph Validation

This guide explains the graph-specific validation layer for report templates.

Read this after:

1. `lx_dtypes/data/report_template_examples/README.md`
2. `docs/guides/report-template-infrastructure.md`

This guide is not about runtime report validation. It is about validating and exporting the structure of already-loaded report templates as a graph.

## What It Is For

- Keep report templates as the source of truth.
- Provide deterministic structural validation with actionable errors/warnings.
- Expose a stable graph contract for assistive scoring (Markov-style next-node ranking).

## Where It Sits In The Pipeline

The order is:

1. YAML is loaded into typed `KnowledgeBase` models.
2. Template structure can be validated generally.
3. Graph validation builds a graph-shaped representation from that structure.
4. Runtime validation, separately, evaluates actual examination payloads.

Use graph validation when you care about template topology.

Do not use it when your real question is "does this reported examination satisfy the validators?"

## Contracts
Models are available in:
- `lx_dtypes.models.knowledge_base.report_template.ReportTemplateGraph`
- `lx_dtypes.models.knowledge_base.report_template.ReportTemplateGraphDataDict`
- `lx_dtypes.models.knowledge_base.report_template.ReportTemplateStructureValidationResult`

Helper functions:
- `build_report_template_graph(...)`
- `validate_report_template_structure(...)`
- `validate_report_template_knowledge_base(...)`

## Example
```python
from pathlib import Path

from lx_dtypes.models.interface.DataLoader import DataLoader
from lx_dtypes.models.knowledge_base.report_template import (
    validate_report_template_knowledge_base,
)

loader = DataLoader(input_dirs=[Path("./lx_dtypes/data/")])
loader.load_module_configs()
kb = loader.load_knowledge_base("report_template_examples")

results = validate_report_template_knowledge_base(kb)
for template_name, result in results.items():
    print(template_name, "ok:", result.ok)
    for issue in result.issues:
        print(issue.level, issue.code, issue.message)
```

## What It Checks

Validation currently reports:
- missing section references
- duplicate section references
- empty template sections
- empty section findings
- invalid finding references
- unknown finding references (warning)

Errors set `result.ok = False`; warnings keep `result.ok = True`.

## How To Read The Result

- `ok = False`
  Structural graph issues were found.
- warnings only
  The template may still load and export, but the graph contains suspicious wiring.

Typical usage:

- authors use it before rollout
- maintainers use it in tests and CI
- downstream ranking/recommendation code uses the graph contract after validation

## Relationship To Other Guides

- System overview: `docs/guides/report-template-infrastructure.md`
- Authoring quickstart: `lx_dtypes/data/report_template_examples/README.md`
- Operator migration: `docs/guides/report-template-findings-validator-migration.md`
