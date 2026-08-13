# Cross-Layer Validation Contract

`lx_dtypes` owns the validation contract shared by knowledge-base artifacts,
ledger payloads, persistence adapters, and frontend applications. A consumer
should receive one canonical, validated shape rather than reconstructing domain
rules from loose dictionaries.

## Boundary rule

- Parse YAML and other external data into the owning `lx_dtypes` model once.
- Pass the validated model inward; do not retain the original mapping as a
  parallel representation.
- Reject unknown fields, empty semantic names, duplicate identities, invalid
  values, and dangling terminology references before persistence or UI state
  mutation.
- Serialize public payloads with snake_case field names. Frontends may convert
  those names in one named transport adapter, but the API schema remains
  canonical.
- Persistence applications own database constraints and transactions. They must
  revalidate data read from mutable JSON or legacy storage before exposing it as
  a current contract.

## Knowledge-base snapshots

`CoreConceptCollection` is the reviewable terminology snapshot consumed by
persistence and frontend applications. It includes both entities and every
type collection referenced by them, including `classification_type` and
`examination_type`. Real knowledge-base exports also carry the complete
`knowledge_base_module` and `knowledge_base_version` identity used by ledger
and persistence contracts. `module_name` remains the stable collection key and
must match `knowledge_base_module` when the identity is present.

Collection validation guarantees:

- concept names are non-empty and unique within a concept kind;
- UUIDs, when supplied, do not identify multiple concepts;
- relation lists contain non-empty, unique semantic names;
- every relation resolves to an exported concept in the same snapshot; and
- unknown fields are rejected.

`kb_to_core_concepts_payload()` performs this validation when exporting a
loaded knowledge base. `canonical_payload_to_storage()` validates an incoming
snapshot before producing storage-oriented records. An incomplete graph is
therefore rejected on either side of the contract boundary.

## Localization ownership

Localization is domain data, not frontend presentation inference:

- `ReportTemplateSection` exports `title_de` and `title_en`. Shipped templates
  provide reviewed titles in both languages.
- `ExaminationCatalogDTO` and `IndicationCatalogDTO` export `name_de` and
  `name_en`, including their related terminology items.
- Legacy records without translations receive a semantic-name fallback inside
  `lx_dtypes`; clients must not turn snake_case identifiers into display text.
- The report language selects between canonical localized values. It does not
  authorize a frontend-owned translation table.

## Ledger and persistence alignment

Ledger write models enforce clinical value invariants before database mutation.
Terminology references in those models are semantic names; the host persistence
service resolves them against the same versioned knowledge-base identity used
to produce `CoreConceptCollection`. Database-generated identifiers and
timestamps belong to the validated response, not to an untrusted request.
For persisted reports, `language`, `knowledge_base_module`, and
`knowledge_base_version` are provenance fields and must be stored as typed
columns by the host application rather than only inside editor JSON.

This package does not own application transactions, ORM relations, or frontend
state. Those layers can rely on the validated contract but remain responsible
for authorization, atomic persistence, and presentation behavior.

## Consumer review checklist

For every field change, review all of the following:

1. the knowledge-base YAML/model and its relation target;
2. the canonical `lx_dtypes` contract and public export;
3. the ledger or other runtime payload using the concept;
4. the host persistence resolver and round-trip response;
5. the frontend transport type and its single normalization adapter; and
6. negative tests for unknown fields, duplicate identity, and missing targets.

Do not add a frontend fallback for a missing canonical collection. Extend the
owning `lx_dtypes` contract and update the versioned consumer window instead.
