# Knowledge-Base Graph API

Owner: `lx-data-models` maintainers  
Canonical topic: immutable frontend projections of versioned knowledge bases

The graph API compiles authored YAML into a deterministic, typed projection.
It keeps module resolution, validation, relationship traversal, and report
template publication rules in the backend. Frontends do not need to understand
module dependencies or perform joins across separate terminology endpoints.

This contract is graph-shaped but storage-agnostic. It does not require a graph
database and does not expose Cypher, database identifiers, or persistence details.

## Endpoints

```text
GET /base_api/knowledge-bases/{module}/{version}/graph
GET /base_api/knowledge-bases/{module}/{version}/examinations/{name}/reporting-context
```

Both routes require an exact module and version. Resolution is fail-closed; the
API does not silently substitute the active version.

## Complete graph snapshot

The graph response uses contract version `knowledge_base_graph_v1` and contains:

- the resolved `knowledge_base_module` and `knowledge_base_version`
- a deterministic `sha256:` snapshot identifier
- declaring module names for provenance
- typed core-concept collections
- compiled, published report templates
- sorted typed edges between semantic names

Edges describe relationships such as `has_finding`, `has_classification`,
`has_choice`, `has_descriptor`, `uses_unit`, and `for_examination`. Semantic
names are stable node identities; database primary keys are optional concept
metadata and are not used for graph traversal.

The snapshot identifier hashes canonical JSON content. The same validated
module version and publication state therefore produces the same identifier.

## Examination reporting context

The reporting-context route returns a closed projection for one examination. It
starts from the resolved examination and includes the transitive concepts needed
by a reporting UI:

```text
examination
  -> findings -> classifications -> choices -> descriptors -> units
  -> indications -> classifications/interventions
  -> examination, finding, indication, intervention, and unit types
  -> compiled published report templates
  -> provenance catalogs
```

The response includes both the source graph's `graph_snapshot_id` and its own
deterministic `context_id`. This lets a frontend cache by exact identity and
detect stale context without comparing individual collections.

An unknown examination returns `404`. An identity mismatch or graph that cannot
be validated returns `409` rather than a partial response.

## Frontend consumption

For reporting, prefer the reporting-context endpoint over independently fetching
examinations, findings, classifications, choices, units, and templates. Store
the returned identity and snapshot identifier with the client-side context.

Use the complete graph endpoint for terminology browsers, dependency views,
provenance inspection, and impact analysis. The frontend should treat edges as
navigation metadata and typed collections as the renderable records.

## Storage boundary

YAML remains the authored and reviewed source. The API projection is immutable
derived data and owns no patient or report-draft persistence. A graph database
may later cache or index the same contract for large arbitrary traversals, but
it must remain an implementation detail behind these endpoints.
