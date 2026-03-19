# Findings Validator Operator Migration

As of March 16, 2026, findings-validator operators use a canonical namespace with
three runtime-supported values:

- `exists`
- `missing`
- `condition`

Legacy operator strings are not part of the supported persisted contract anymore.

Historical aliases that should be migrated away:

- `present` -> `exists`
- `absent` -> `missing`
- `not_exists` -> `missing`
- `not-exists` -> `missing`
- `not exists` -> `missing`
- `if` -> `condition`

## Why This Changed

The runtime validator engine only implements three behaviors:

- `exists`
- `missing`
- `condition`

The extra names looked like distinct operators, but they were aliases rather than
independent runtime semantics. Keeping them as first-class operator values made the
contract harder to reason about and weakened static typing.

## Breaking Change Scope

If downstream template JSON or YAML still stores `present`, `absent`, or
`not_exists` as persisted operator values:

- strict model validation can reject those values,
- runtime behavior should not rely on those aliases,
- downstream data should be migrated to canonical operator names before loading.

Downstream code should migrate stored templates to canonical operators now.

## Migration Script

Use:

```bash
python lx-data-models/scripts/migrate_findings_validator_operators.py path/to/templates
```

Check mode for CI:

```bash
python lx-data-models/scripts/migrate_findings_validator_operators.py --check path/to/templates
```

In-place rewrite:

```bash
python lx-data-models/scripts/migrate_findings_validator_operators.py --write path/to/templates
```

The script scans `.yaml`, `.yml`, and `.json` files and rewrites only
findings-validator-shaped objects.

It preserves the data model, but not YAML comments or original formatting. The
current implementation serializes through `PyYAML`, so downstream users should
expect a broader textual diff than just the operator value change.

## Expected Data Shape After Migration

Before:

```yaml
- model: findings_validator
  name: polyp_present
  finding: esophagus_polyp
  operator: present
  query:
    finding: esophagus_polyp
    operator: present
```

After:

```yaml
- model: findings_validator
  name: polyp_present
  finding: esophagus_polyp
  operator: exists
  query:
    finding: esophagus_polyp
    operator: exists
```

Negative aliases normalize to `missing`:

```yaml
operator: absent
```

becomes:

```yaml
operator: missing
```

## Comparator Note

`not_in` remains a supported canonical comparator for conditional clauses. This
migration only changes operator names, not comparator semantics.

## Authoring Note

This migration guide is for maintainers of YAML/JSON template data.

It should not be interpreted as evidence that raw template YAML is ready for
non-technical self-service editing. At the current repository state, operator
migration and validator authoring remain technical maintenance tasks.
