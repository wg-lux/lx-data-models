# Report-template example package

Owner: lx_dtypes maintainers. This package contains executable examples and
synthetic test data for report-template structure, validators, and coverage.
All current examples resolve against their terminology dependencies. The minimal
`base_report_template` and `ukw_gastroscopy` examples reuse the STAR upper-GI
examination and esophageal mucosal-status finding through `base_required_section`.
Their names do not establish a clinically approved or institution-approved protocol.
The package owns reporting references only; its extra illustrative concepts are
owned by `report_template_examples_terminology`. Provenance is recorded in
`data/definitions.yml` under `source_provenance`.

For authoring instructions and the ColoReg findings-validation trace, read
[Making report templates and tracing findings issues](../../../../docs/guides/report-template-authoring.md).
That guide is the canonical quickstart; the YAML in this directory is the
reference example, not a clinical fallback or a runtime builder write target.

Start with [package structure](../../../../docs/guides/dtypes-package-structure.md)
for manifests and dependencies. See
[report-template infrastructure](../../../../docs/guides/report-template-infrastructure.md)
for loading, export, and runtime internals. Copy examples to an editable,
versioned package before adapting them; installed wheel content is immutable.
