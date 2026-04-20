# Runtime Output vs Canonical `ddict`

This guide explains why the validator runtime execution payloads in
`lx_dtypes/models/knowledge_base/report_template/ValidatorRuntime.py`
do not use the canonical `ddict` shape with a `uuid`.

## Short Answer

Canonical `ddict` objects represent stable domain entities.

Runtime execution payloads represent derived evaluation results for one
specific validation run.

Those are different categories of data and should not be modeled the same way.

## Canonical `ddict` Means Stable Identity

In this repository, a canonical `ddict` is used for objects such as:

- `Classification`
- `ClassificationChoice`
- `ReportTemplate`
- `PExamination`

These objects have a stable identity across:

- parsing
- serialization
- syncing
- persistence adapters
- API export

That is why a canonical object can justify fields such as:

- `uuid`
- `name`
- `source_file`
- `kb_module_name`

These fields describe the thing itself.

## Runtime Execution Payloads Are Not Domain Objects

The execution payloads returned by the runtime validator engine describe:

- whether validation passed
- which validator was evaluated
- how many occurrences matched
- how many conditions triggered
- which issues were produced
- which dependencies failed

Examples:

- `FindingsValidatorExecutionDataDict`
- `ClassificationValidatorExecutionDataDict`
- `ExaminationValidatorExecutionDataDict`
- `ReportTemplateRuntimeValidationResultDataDict`

These values are:

- derived from input
- request-scoped
- ephemeral
- safe to recompute

They do not describe a stable knowledge-base object.

## Why No `uuid`

Adding a canonical-style `uuid` to runtime execution payloads would imply a
kind of identity they do not actually have.

Problems this creates:

- It suggests persistence semantics where none exist.
- It suggests referential stability across runs.
- It makes the runtime output look like a stored entity instead of a computed result.
- A random `uuid` adds noise without helping reconstruction or validation.

For example:

- If the same validator is run twice against two different payloads, the result
  is not "the same object with updated fields".
- It is two different execution snapshots.

That distinction is important.

## Correct Mental Model

Use this split:

- canonical model = noun
- runtime execution payload = evaluation record

A canonical model answers:

- what object exists?

A runtime execution payload answers:

- what happened when this validator was run?

This mirrors the package boundary used elsewhere in the repo:

- Django ORM models are persistence adapters
- Pydantic models and `ddict`s represent canonical package data
- runtime result payloads represent derived execution state

## When Stable IDs Would Be Reasonable

There are valid cases where runtime output may need stable identifiers:

- persisted validation runs
- audit history
- reviewer acknowledgement workflows
- cross-request UI caching
- linking a specific issue from another system

If that requirement appears, the recommended approach is:

1. keep runtime execution payloads separate from canonical `ddict`s
2. add execution-specific identifiers such as:
   - `run_id`
   - `result_id`
   - `issue_id`
3. make those identifiers deterministic only if the consuming workflow needs it

Do not reuse canonical entity identity just because an execution record also
needs a key.

## Practical Rule

Use canonical `ddict` with `uuid` when the object is part of the domain model.

Use runtime execution payloads without canonical identity when the object is a
derived validation result.

If runtime output needs persistence later, define a dedicated execution schema
instead of forcing it into the canonical model shape.
