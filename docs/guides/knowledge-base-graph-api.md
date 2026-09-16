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

## Repeated resolution and integrity

Hosts performing repeated queries can retain an explicit index of one snapshot:

```python
from lx_dtypes.models.contracts import KnowledgeBaseGraphResolver

resolver = KnowledgeBaseGraphResolver(snapshot)
context = resolver.reporting_context("colonoscopy")
```

Construction validates and isolates the snapshot, including its content hash,
concept relationships, and published template references. Returned contexts do
not share mutable state with the resolver. Recreate the resolver when the source
snapshot changes; cache lifetime, memory limits, authorization, and eviction
belong to the host. There is no implicit global cache. The existing
`build_examination_reporting_context` helper constructs a resolver for one call.
The HTTP routes retain a separate `KnowledgeBaseGraphRouteCache` per route
registration (eight identities by default). Graph and reporting-context requests
share each validated snapshot and index; responses are serialized afresh.
Every request still calls the knowledge-base loader. Reuse requires the same
exact module/version and the same resolved source object. Replacement sources
rebuild the projection; loader failures evict it and propagate without fallback.
Hosts returning a fresh knowledge-base object on every load will rebuild each time.

The standard API clears this cache through its existing template save/publication
and terminology mutation hooks. Custom hosts can pass an explicitly owned cache:

```python
from lx_dtypes.django.api.knowledge_base_graph_routes import (
    KnowledgeBaseGraphRouteCache,
    register_knowledge_base_graph_routes,
)

cache = KnowledgeBaseGraphRouteCache(max_entries=4)
register_knowledge_base_graph_routes(api, load_module_kb=loader, graph_cache=cache)
# After changing source data and invalidating the host's loader cache:
cache.clear()
```

Entries are evicted in least-recently-used order. The limit bounds entry count,
not bytes: each entry retains its source, snapshot, and isolated resolver copy.
Loading and cold compilation are serialized per cache, preventing duplicate cold
builds and making `clear()` wait for active compilation before evicting it.
Context traversal and serialization occur outside that lock. Requests already
holding a projection may finish with that coherent snapshot after invalidation.
Hosts requiring a stronger publication barrier must coordinate in-flight requests.

Treat loaded sources as immutable between invalidations. In-place edits are not
detected by object identity, and there is no filesystem watcher or TTL. External
updates must invalidate both loader and graph caches in every worker (or reload
those workers). The package does not implement cross-process invalidation or host
authorization. Do not share a cache across differently authorized source views
unless the loader enforces that boundary on every request.

Index construction processes the full graph. Subsequent context queries traverse
selected records and their edges, plus the retained provenance catalogs; output
validation and serialization still scale with the returned context size.
Run `python scripts/benchmark_graph_resolution.py` for deterministic synthetic
fixtures and local timings. These timings do not establish a production SLA.

Snapshot construction no longer mutates exporter-owned dictionaries and sorts
concept collections by semantic name. This can change snapshot IDs for previously
unsorted collections, so hosts must refresh cached contexts. Imported snapshots
with stale hashes, missing or invented edges, duplicate templates, or unpublished
templates now fail validation. Hashes establish content consistency, not trusted
authorship or clinical validity. Predicted edges must remain separate proposals;
the canonical graph accepts only declared terminology relationships.

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
