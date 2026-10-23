# Cross-Layer Validation Contract

`lx_dtypes` owns the validation contract shared by knowledge-base artifacts,
ledger payloads, persistence adapters, and frontend applications. A consumer
should receive one canonical, validated shape rather than reconstructing domain
rules from loose dictionaries.

This contract is maintained by the `lx_dtypes` maintainers and is the canonical
guide to advisory validation and strict boundary validation.

## Single source of truth

The knowledge-base model registry defines supported package records; the parser
owns aliases; `KnowledgeBaseConfig` and `DataLoader` own manifest normalization
and dependency selection. Authoring checks consume these definitions rather than
maintaining a second schema or dependency resolver. `CoreConceptCollection`
owns concept-graph invariants, and the reporting readiness engine owns template
publication checks.

For one explicit manifest, `lx_dtypes.packages.validate_package` composes those
checks with optional ledger examinations through `assess_examination`. It does
not introduce another clinical rule engine. Invalid package graphs prevent ledger
assessment. Creation and strict loading use the same package check as the `ok`
CLI; the [package workflow](dtypes-package-structure.md#create-load-and-validate-from-python)
documents the public API and its distinction from runtime registry loading.

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

Both `validate_contract()` and `assess_examination()` accept a keyword-only
`language="de"` or `language="en"`. They use the shared default from
`lx_dtypes.language` (German); callers needing the previous English boundary
messages must pass `language="en"`. Unsupported languages raise `ValueError`,
including for valid payloads. `assess_examination()` forwards the selection to
study validation, so contract, terminology, and study messages share one language.
Codes, paths, severity, and validation decisions are unchanged.

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

## Complete package persistence

`build_package_snapshot(kb)` and `restore_package_snapshot(snapshot)`, exported
from `lx_dtypes.models.contracts`, preserve all registered knowledge-base record
families using their owning models. This includes validators, study presets,
reference catalogues and optional employee definitions in addition to the
frontend concept graph. Snapshots retain exact resolved module versions and
report-template lifecycle states, validate canonical graph relationships, and
exclude local source and data paths.

Hosts compare the semantic `snapshot_id` when enforcing immutable imports.
Digest normalization excludes runtime UUID/timestamp metadata on owning
`AppBaseModel` instances; it does not discard similarly named keys from arbitrary
domain payloads. Persisted snapshots are validated again before restoration.
Older projection-only receipts remain readable but cannot reconstruct omitted
package families; they must not be silently presented as complete snapshots.
The snapshot contract requires an explicit migration when the runtime model-family
registry changes; missing families are not filled from current package files.
Persistence tables, access control and import transactions remain host-owned.

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

## Study collection persistence

`lx_dtypes.models.contracts.StudyCollectionRecord` binds the existing
`DtypesRecordPersistencePayload` and `ValidationReport` to persistent study,
optional cohort, and host examination UUIDs. It requires complete matching KB
identities, assessment time and language, and the report template name whenever
study rules were evaluated. Contract or terminology errors prevent collection;
failed study criteria remain valid observations and retain their original issues.
Ledger UUIDs and host examination UUIDs are separate identities.
The required `package_snapshot_id` pins the immutable `PackageSnapshot` digest
used for assessment. Hosts resolve this reference to their preserved snapshot and
verify its digest before evaluating or restoring collection data.
Canonical `StudyDefinition` and optional `CohortDefinition` snapshots preserve
the definitions at collection time; cohort identity and definition are paired.

Hosts compute the report with `assess_examination` against the selected package
and supplied ledger before constructing the record. The contract verifies shape
and provenance consistency; it cannot prove that an externally supplied report
was actually computed for that ledger. Hosts must verify study/cohort membership
and examination/patient linkage, and store the observation and assessment
atomically. Raw ledger descriptor values are retained without substituting study
results. Read JSON with `StudyCollectionRecord.model_validate_json`; normal
`model_dump_json` round trips include and verify the report's computed `ok` value.

## Dataset study statistics

`StudyMetadata.analysis_definitions` carries versioned
`StudyAnalysisDefinition` objects alongside authored hypotheses. Definitions
declare an exact terminology identity, the finding used as the analysis unit,
population rules, comparison groups and explicit positive/negative endpoint
rules. Every analysis dependency must also appear in
`terminology_requirements`. Drafts may describe unresolved protocol decisions;
they cannot produce statistics until those decisions have been resolved.
An absent or empty analysis list preserves legacy setup and package digests;
authored analysis rules become part of their content identity.

`lx_dtypes.stats.evaluate_study_dataset` validates definitions against the
knowledge base and evaluates authorized canonical ledger examinations. Rules
combine bounded predicates with `all` or `any`; no Python, SQL or arbitrary
expressions are accepted. Missing inputs remain unknown rather than becoming
negative outcomes. Results retain the analysis digest and exact KB identity,
population exclusions, ambiguous group assignments and per-endpoint numerator,
denominator, missingness and conflict counts. A zero denominator produces
`rate=None`.

The host owns dataset access and candidate membership. It must report missing
ledger records and records excluded for a different terminology version, and
must not substitute the current active package for historical observations.
The lx-annotate cohort editor saves these same definitions and requests server
evaluation over the complete authorized dataset scope, independently of the
paginated examination preview.

For ColoReg, `assemble_coloreg_analysis_units` binds the original polyp,
index resection and follow-up roles using explicit lesion references. Missing
or out-of-scope history remains unavailable. The
[ColoReg specification](coloreg-resection-study.yml) owns endpoint meanings,
protocol decisions and denominator choices.

This is a descriptive statistics method, not a hypothesis significance test.
Additional methods can consume the versioned definitions, validated analysis
units and typed results without adding a second terminology or ledger
validator. Inferential estimates, patient-level clustering, observation-window
event aggregation and protocol adjudication require their own explicit method
contracts; this implementation does not infer them from a displayed rate.

## Study exchange and researcher spreadsheets

`StudyExchangeBundle` is the shared evidence contract for hub transfer and
Excel. It contains current study/cohort definitions, historical
`StudyCollectionRecord` observations and assessments, exact `PackageSnapshot`
dependencies, and persistent patient/examination UUID links. Historical
definitions remain distinct from currently edited definitions. Local study
primary keys, dataset primary keys and sender permissions are not portable.

The bundle validates dependency closure and recomputes each assessment through
the canonical knowledge base and ledger validator. Hosts convert local ledger
patient references to persistent UUIDs on export and resolve them back only
within the receiving researcher's authorized scope. A receiving host must
already have the exact package snapshots and matching patient/examination
identities. Import is explicit and transactional; conflicting content is never
merged by guessing, and an identical replay is idempotent.

```python
from lx_dtypes.study_exchange import (
    parse_study_exchange,
    study_exchange_from_xlsx,
    study_exchange_to_xlsx,
)

bundle = parse_study_exchange(canonical_json)
workbook_bytes = study_exchange_to_xlsx(bundle)
restored = study_exchange_from_xlsx(workbook_bytes)
```

The workbook provides readable definitions, collection provenance, repeated
finding identities, typed scalar observations, units and evaluation issues.
Chunked canonical JSON retains the complete contract. Strings are literal
cells, and archive, worksheet and cell bounds prevent silent truncation.
Import verifies readable sheets against the canonical representation and
rejects formulas or edited projections. This workbook is a lossless exchange
format, not a second editable ledger.

For existing or edited research spreadsheets, use the separate, existing
`TableMapping` contract in `lx_dtypes.models.contracts.table_import`. Explicit
column names and `values` mappings translate local wording to exact-version
concept identifiers. A classification may use the original column shorthand,
or `choice` plus a `descriptors` mapping. Each descriptor names its source
column and source representation (`text`, `integer`, `number`, `boolean` or
`selection`); its knowledge-base definition remains authoritative for type,
bounds and admissible values. The parser converts source representation and
delegates value validation to that owning definition. It does not invent
terminology or execute mapping expressions.

These transports share the same stored collections. Host workflows explicitly
capture validated ledger observations before export; export itself does not
create evidence. Receiving a hub archive does not assign a local owner or
activate a cohort. The authenticated receiving researcher accepts it through
the same host import service used for workbooks.

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
