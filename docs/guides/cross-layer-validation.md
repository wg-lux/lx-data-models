# Cross-Layer Validation Contract

`lx_dtypes` owns the validation contract shared by knowledge-base artifacts,
ledger payloads, persistence adapters, and frontend applications. A consumer
should receive one canonical, validated shape rather than reconstructing domain
rules from loose dictionaries.

This contract is maintained by the `lx_dtypes` maintainers and is the canonical
guide to advisory validation and strict boundary validation.

## Advisory validation during data capture

Use `lx_dtypes.validation` when incomplete or inconsistent input should produce
feedback without interrupting the caller:

```python
from lx_dtypes import load_knowledge_base
from lx_dtypes.validation import assess_examination

kb = load_knowledge_base("report_template_examples")
report = assess_examination(
    kb,
    {
        "patient": "synthetic_patient",
        "examination": "star_upper_gi_endoscopy",
        **kb.config.knowledge_base_identity.model_dump(),
    },
    template_name="star_upper_gi_main",
)
print(report.model_dump(mode="json"))
```

The knowledge base owns terminology and predefined study rules. The ledger owns
observations and their terminology provenance. Contracts own the exchange shape.
`assess_examination` connects these layers without writing data or changing the
input. It reuses the existing semantic admissibility and report-template engines,
including conditional requirements, classifications, interventions, and units.

`validate_contract(Model, payload)` supports any owning Pydantic contract,
including `StudySetupDefinition`. It returns a typed `value` on success and a
`ValidationReport` on both success and failure. It retains the owning model's
strictness; it does not make a permissive model strict. Mutable model instances
are reparsed. Study setup definitions select datasets and cohorts; report-template
validators define runtime study rules. These are distinct contracts.

Reports have a versioned shape (`schema_version="1.0"`) and ordered issues with
`code`, `message`, `level`, `source`, `path`, and optional `validator_name`.
Consumers branch on codes, display messages, and use paths to identify contract
fields. `ok` means no error-level findings; warnings remain visible. It is not
authorization to persist or a statement of clinical correctness.

Boundary messages are centralized in `lx_dtypes/validation_messages.yml`.
Contract issue codes retain Pydantic's error type with a `contract.` prefix.
Unknown error types use a generic constraint message; submitted values and
custom exception context are excluded. Study issue codes and messages come
directly from the existing runtime engine, so hosts need no second rule or
message implementation. Study messages may contain terminology names.

| Condition | Result |
| --- | --- |
| Malformed ledger payload | Contract issues; no terminology or study evaluation |
| Missing or incomplete legacy KB identity | Warning; evaluation may continue |
| Any supplied KB identity component conflicts | Error; no study evaluation |
| Unknown template | Error; no study evaluation |
| Inadmissible terminology relationship | Error; no study evaluation |
| Valid terminology with unmet study rules | Study findings; `study_evaluated=true` |

`study_evaluated=false` must not be displayed as a passed study. With no template,
the API checks semantic admissibility only. Semantic validation currently reports
the first failure from the strict engine; runtime study evaluation collects its
available findings. Loading a broken knowledge base and programming errors still
raise: the advisory API catches expected payload and semantic validation failures
only. Existing strict APIs retain their behavior.

## Boundary rule

- Parse YAML and other external data into the owning `lx_dtypes` model once.
- Pass the validated model inward; do not retain the original mapping as a
  parallel representation.
- At persistence and exchange boundaries, reject unknown fields, empty semantic names, duplicate identities, invalid
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
- descriptor numbers are finite and descriptor ranges, selection cardinalities,
  default options, and probabilities are internally consistent;
- unknown fields are rejected.

Knowledge-base descriptor models historically use positive and negative
infinity as in-memory sentinels for an unbounded numeric range. The canonical
snapshot adapter converts those sentinels to `null`; direct canonical payloads
containing `NaN` or infinity are rejected. Persistence and frontend consumers
therefore receive standards-compliant JSON without reconstructing sentinel
semantics.

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
