# Knowledge-Base Contract Migration

This guide documents how patient-based and reporting endpoints should migrate
away from direct `DataLoader` usage and toward the typed, version-aware
KnowledgeBase resolver contract.

## Goal

Runtime API code must not load YAML directly through ad-hoc `DataLoader`
instances. Endpoints that validate patient findings, report templates, or
patient examination payloads must resolve one explicit knowledge-base identity:

- `knowledge_base_module`
- `knowledge_base_version`

The API may accept payloads without a version for backwards compatibility, but
the boundary must normalize them to the current configured KB identity before
loading or validating data.

The main frontend caller is:

`/home/admin/dev/lx-annotate/frontend/src/components/VideoExamination/VideoExaminationAnnotation.vue`

That caller can continue to send the existing route payloads while the API fills
the current KB version. New frontend work should include both
`knowledge_base_module` and `knowledge_base_version` once the selected
terminology bundle is known.

## Current Contract

Use `lx_dtypes.models.contracts.KnowledgeBaseContract` for API route loaders.
The contract intentionally exposes only the KB methods used by patient and
reporting endpoints:

- `export_core_concepts`
- `export_report_template`
- `export_report_template_preview`
- `get_report_template_lifecycle_status`
- `evaluate_report_template_validators`
- `report_template`

Use `lx_dtypes.models.interface.KnowledgeBaseResolver` to load KBs:

```python
from lx_dtypes.models.interface.KnowledgeBaseResolver import (
    get_knowledge_base_identity,
    load_knowledge_base,
)

module_name, version = get_knowledge_base_identity("report_template_examples")
kb = load_knowledge_base(module_name, version=version)
```

For prototype or builder-only directories, pass `input_dirs` to the resolver
instead of constructing a `DataLoader` in route code.

## Ownership Boundary

Endoreg DB remains the persistence owner for patient-specific runtime state.
`lx-data-models` owns the typed contracts, canonical KB models, version-aware
KB loading, and runtime validation semantics. It must not become the write owner
for patient examinations, patient findings, uploaded media, report documents, or
annotation state.

The boundary should look like this:

- Endoreg DB persists patient and examination rows, findings selected by users,
  report drafts, media links, and audit-relevant workflow state.
- `lx-data-models` validates and serializes typed payloads such as
  `PExamination`, core concepts, report-template exports, and validator
  results.
- The Django API in `lx_dtypes.django.api.main` is an integration adapter. It
  may read Endoreg-owned ORM rows through configured host models, but should
  immediately convert them into typed `lx_dtypes` contracts before evaluating
  KB logic.
- Knowledge-base YAML is a terminology/version artifact, not patient state.
  Runtime routes must load it through `KnowledgeBaseResolver` and must not
  mutate it as part of patient workflows.

## Migration Rules

1. Do not import `DataLoader` in Django API route modules. The Endoreg DB KB
   identity helper now resolves the configured module/version through
   `KnowledgeBaseResolver` instead of constructing a `DataLoader`.
2. Resolve the KB identity once at the API boundary.
3. Reject a payload module that conflicts with the route module.
4. Prefer the payload version when present.
5. Otherwise prefer the active terminology selection.
6. Otherwise use `get_knowledge_base_identity(module_name)` and load that
   version. Builder flows should do the same so module loading is always
   version-explicit, even when the UI is only addressing a module name.
7. Register runtime lookup tracking only after the resolver returns a KB.
8. Keep patient payloads typed as `PExamination`.
9. Add tests that monkeypatch `load_knowledge_base` and assert the expected
   `version` argument.

## Recommended Thinning And Optimization

The following areas can be reduced or moved without changing persistence
ownership:

- Thin `lx_dtypes.django.api.main`: keep route registration, host-model lookup,
  cache clearing, and KB identity resolution there; move serialization helpers
  such as `_serialize_choice`, `_serialize_classification`, and
  `_serialize_patient_finding` into typed contract adapters.
- Make builder-side report-template loading version-explicit through
  `KnowledgeBaseResolver` before calling `load_knowledge_base`; avoid relying
  on module-name-only loads in runtime API code.
- Cache findings-route core concepts by `(module_name, version)` rather than
  module name alone once the resolved KB version is available on the loaded
  contract.
- Resolve imported terminology bundles to an explicit version before reloading
  them for validation, instead of validating the import with a module-name-only
  load.
- Include the resolved knowledge-base identity in runtime validator responses
  so callers can see which KB version produced the result.
- Include the resolved knowledge-base identity in the core-concepts response so
  callers can see which KB module/version produced the exported terminology.
- Collapse duplicate KB lookup helpers: `_kb_core_concepts`, `_kb_lookup`, and
  `_norm_name` currently exist in both `main.py` and `findings_routes.py`.
  Prefer one typed lookup adapter built from `CoreConceptCollection`.
- Replace `Dict[str, Any]` route responses with Pydantic contracts where the
  frontend depends on a stable shape. Good first candidates are findings lists,
  classification lists, report-template validation responses, and core-concepts
  payloads.
- Keep `DataLoader` for authoring tools, tests, and low-level resolver internals
  only. New runtime API code should depend on `KnowledgeBaseResolver` or a
  narrow callable returning `KnowledgeBaseContract`.
- Move host ORM introspection behind a small protocol or adapter owned by the
  Endoreg integration layer. This makes it explicit that lx-data-models consumes
  persisted rows but does not own their schema lifecycle.
- Cache by KB identity, not only module name. Any cache holding exported core
  concepts or report templates should include `(module_name, version)` once the
  route surface starts exposing multiple active versions concurrently.
  Findings-route lookups now follow that rule for KB-exported core concepts.
- Prefer typed conversion at the edge: convert Endoreg DB rows to
  `PExamination` once, then pass that object inward. Avoid passing ORM objects
  into report-template validators.

## Frontend Migration Notes

`VideoExaminationAnnotation.vue` can keep using current endpoints during the
transition because the API now resolves missing versions to the current
configured KB identity. The frontend should still migrate toward sending:

- `knowledge_base_module`
- `knowledge_base_version`

with patient-examination/report-template validation payloads once the selected
terminology bundle is known in the UI state. That makes validation replayable:
the same patient payload can be evaluated later against the exact KB version
used during annotation.

Do not make the frontend infer the version from labels or template names. The
version must come from the terminology bundle selection or from the
patient-examination record returned by Endoreg DB.

## Remaining Work

- Audit all Django API modules for direct `DataLoader` imports. Runtime route
  modules should not import it; builder/test/helper modules may still use it
  where they are explicitly constructing authoring fixtures. The Endoreg DB
  KB identity helper has already moved off `DataLoader`; keep following that
  pattern in remaining runtime code.
- Move any remaining unstructured response dictionaries into
  `lx_dtypes.models.contracts` Pydantic models when they cross API boundaries.
- Extend the frontend to send `knowledge_base_version` with patient examination
  and report-template validation payloads.
- Keep tightening terminology import/export paths so every runtime KB reload is
  version-explicit.
- Surface resolved KB identity in validation responses during the migration
  window, then make client-side version selection mandatory for new write
  paths.
- Surface resolved KB identity in core-concepts responses during the migration
  window as well, so module-only lookups stay auditable.
- Add contract tests for `/base_api/examinations/.../findings/`,
  `/base_api/findings/.../classifications/`, and `/base_api/patient-findings/`
  once those routes expose the active KB identity in their request or route
  context.
- Treat missing or mismatched KB versions as validation failures, not silent
  fallback behavior.
- Add route-level tests for the Endoreg DB integration adapter that assert ORM
  rows are converted to `PExamination` before report-template validation.
- Decide whether current-version fallback should eventually become a hard
  client requirement. A safe deprecation path is: log missing versions, expose
  response metadata with the resolved identity, require frontend versions for
  new write paths, then reject missing versions for clinical/audit workflows.

## Completed Passes

- `lx_dtypes.django.api.report_template_routes._load_builder_module_kb` now
  resolves builder knowledge bases through
  `lx_dtypes.models.interface.KnowledgeBaseResolver.load_knowledge_base`
  with `input_dirs` instead of instantiating `DataLoader` directly.
- The route-level regression test now asserts that the resolver receives the
  builder module root as `input_dirs`, keeping the API boundary version-aware.
- `endoreg_db.services.knowledge_base_identity.get_configured_knowledge_base_identity`
  now resolves the configured KB identity through
  `lx_dtypes.models.interface.KnowledgeBaseResolver.get_knowledge_base_identity`
  instead of constructing a `DataLoader` directly.
- `PatientExamination.assign_knowledge_base_identity()` continues to use the
  service boundary and therefore inherits the resolver-based identity lookup.

## Deprecated Pattern

Do not add new route code like this:

```python
loader = DataLoader(input_dirs=[...])
loader.load_module_configs()
kb = loader.load_knowledge_base(module_name)
```

That path can load YAML without the same version identity checks expected by the
runtime API. Use the resolver instead.
