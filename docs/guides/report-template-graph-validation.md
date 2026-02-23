# Report Template Graph Validation

This guide explains how to validate report-template structure and build a typed directed graph for recommendation/scoring.

## Why
- Keep report templates as the source of truth.
- Provide deterministic structural validation with actionable errors/warnings.
- Expose a stable graph contract for assistive scoring (Markov-style next-node ranking).

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

## Current checks
Validation currently reports:
- missing section references
- duplicate section references
- empty template sections
- empty section findings
- invalid finding references
- unknown finding references (warning)

Errors set `result.ok = False`; warnings keep `result.ok = True`.
