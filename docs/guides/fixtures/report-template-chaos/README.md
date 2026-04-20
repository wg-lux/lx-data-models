# Report Template Chaos Fixture

This fixture is intentionally broken. It exists to stress-test auditors and
validator error reporting for the report-template infrastructure.

Location notes:
- Kept under `docs/guides/fixtures/` so it is not auto-discovered by normal
  `DataLoader` scans over `lx_dtypes/data/`.
- You can paste these files directly into the "Input Data to Audit" section of
  your auditor prompt.

## Files

- `config.yaml`
- `report_templates.yaml`

## Run The Auditor

```bash
python scripts/audit_fixture.py \
  --config docs/guides/fixtures/report-template-chaos/config.yaml \
  --data-root lx_dtypes/data
```

## Injected Failure Modes

1. Silent string reference mismatch:
`report_template.report_sections` uses `upper_gi_esophagus`, but the section is
defined as `upper-gi-esophagus`.

2. Dangling references:
missing section and missing validators are referenced from the template.

3. KnowledgeBase collision risk:
duplicate `report_finding.name: normal_finding` in the same module.

4. Alias confusion:
both `finding_validator` alias and canonical `findings_validator` are used.

5. Mixed inline + referenced findings:
a section mixes string references and inline findings.

6. Circular validator chain:
`loop_validator_a` references `loop_validator_b` and vice versa.

7. Depends-on ambiguity:
`depends_on` intentionally omits richer terminology modules that may be needed
for classification-heavy templates.
