from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar

import pytest
from ninja.errors import HttpError

from lx_dtypes.django.api.knowledge_base_graph_routes import (
    register_knowledge_base_graph_routes,
)
from lx_dtypes.models.contracts.json_types import JsonObject
from lx_dtypes.models.ledger.p_examination.Pydantic import PExamination

F = TypeVar("F", bound=Callable[..., Any])


class _RouteRegistry:
    def __init__(self) -> None:
        self.handlers: dict[str, Callable[..., dict[str, Any]]] = {}

    def get(self, path: str) -> Callable[[F], F]:
        def decorator(function: F) -> F:
            self.handlers[path] = function
            return function

        return decorator


class _MinimalKnowledgeBase:
    def __init__(self, *, module_name: str, version: str) -> None:
        self.report_template: JsonObject = {}
        self.findings_validator: JsonObject = {}
        self.classification_validator: JsonObject = {}
        self.intervention_validator: JsonObject = {}
        self.unit_validator: JsonObject = {}
        self.examination_validator: JsonObject = {}
        self.module_name = module_name
        self.version = version

    def export_core_concepts(self) -> JsonObject:
        return {
            "module_name": self.module_name,
            "knowledge_base_module": self.module_name,
            "knowledge_base_version": self.version,
            "examination": [{"name": "gastroscopy"}],
        }

    def export_report_template(self, name: str) -> JsonObject:
        raise AssertionError(f"Unexpected template export: {name}")

    def export_report_template_preview(self, name: str) -> JsonObject:
        raise AssertionError(f"Unexpected template preview export: {name}")

    def get_report_template_lifecycle_status(self, name: str) -> str:
        raise AssertionError(f"Unexpected template lifecycle lookup: {name}")

    def evaluate_report_template_validators(
        self, name: str, p_examination: PExamination
    ) -> JsonObject:
        raise AssertionError(f"Unexpected template validation: {name}, {p_examination}")

    def evaluate_findings_validator(
        self, name: str, p_examination: PExamination
    ) -> JsonObject:
        raise AssertionError(f"Unexpected findings validation: {name}, {p_examination}")

    def evaluate_classification_validator(
        self, name: str, p_examination: PExamination
    ) -> JsonObject:
        raise AssertionError(
            f"Unexpected classification validation: {name}, {p_examination}"
        )

    def evaluate_intervention_validator(
        self, name: str, p_examination: PExamination
    ) -> JsonObject:
        raise AssertionError(
            f"Unexpected intervention validation: {name}, {p_examination}"
        )

    def evaluate_unit_validator(
        self, name: str, p_examination: PExamination
    ) -> JsonObject:
        raise AssertionError(f"Unexpected unit validation: {name}, {p_examination}")

    def evaluate_examination_validator(
        self, name: str, p_examination: PExamination
    ) -> JsonObject:
        raise AssertionError(
            f"Unexpected examination validation: {name}, {p_examination}"
        )


def _registered_routes(
    loader: Callable[..., _MinimalKnowledgeBase],
) -> _RouteRegistry:
    registry = _RouteRegistry()
    register_knowledge_base_graph_routes(registry, load_module_kb=loader)
    return registry


def test_graph_route_arranges_exact_identity_and_asserts_serialized_snapshot() -> None:
    # Arrange
    calls: list[tuple[str, str | None]] = []

    def load(module_name: str, *, version: str | None = None) -> _MinimalKnowledgeBase:
        calls.append((module_name, version))
        return _MinimalKnowledgeBase(module_name=module_name, version=version or "")

    routes = _registered_routes(load)
    route = routes.handlers["/knowledge-bases/{module_name}/{version}/graph"]

    # Act
    payload = route(None, "clinical_reporting", "2.0.0")

    # Assert
    assert calls == [("clinical_reporting", "2.0.0")]
    assert payload["contract_version"] == "knowledge_base_graph_v1"
    assert payload["identity"] == {
        "knowledge_base_module": "clinical_reporting",
        "knowledge_base_version": "2.0.0",
    }
    assert payload["snapshot_id"].startswith("sha256:")


def test_graph_route_arranges_incoherent_loader_and_asserts_http_409() -> None:
    # Arrange
    def load(module_name: str, *, version: str | None = None) -> _MinimalKnowledgeBase:
        del module_name, version
        return _MinimalKnowledgeBase(module_name="different_module", version="9.9.9")

    routes = _registered_routes(load)
    route = routes.handlers["/knowledge-bases/{module_name}/{version}/graph"]

    # Act
    with pytest.raises(HttpError) as error:
        route(None, "clinical_reporting", "2.0.0")

    # Assert
    assert error.value.status_code == 409
    assert "coherent graph snapshot" in str(error.value)


def test_reporting_context_route_arranges_unknown_exam_and_asserts_http_404() -> None:
    # Arrange
    routes = _registered_routes(
        lambda module_name, *, version=None: _MinimalKnowledgeBase(
            module_name=module_name,
            version=version or "",
        )
    )
    route = routes.handlers[
        "/knowledge-bases/{module_name}/{version}/examinations/"
        "{examination_name}/reporting-context"
    ]

    # Act
    with pytest.raises(HttpError) as error:
        route(None, "clinical_reporting", "2.0.0", "colonoscopy")

    # Assert
    assert error.value.status_code == 404
    assert "unknown" in str(error.value)
    assert "colonoscopy" not in str(error.value)


def test_reporting_context_route_arranges_valid_exam_and_asserts_closed_identity() -> (
    None
):
    # Arrange
    routes = _registered_routes(
        lambda module_name, *, version=None: _MinimalKnowledgeBase(
            module_name=module_name,
            version=version or "",
        )
    )
    route = routes.handlers[
        "/knowledge-bases/{module_name}/{version}/examinations/"
        "{examination_name}/reporting-context"
    ]

    # Act
    payload = route(None, "clinical_reporting", "2.0.0", "gastroscopy")

    # Assert
    assert payload["identity"] == {
        "knowledge_base_module": "clinical_reporting",
        "knowledge_base_version": "2.0.0",
    }
    assert payload["examination_name"] == "gastroscopy"
    assert [row["name"] for row in payload["concepts"]["examination"]] == [
        "gastroscopy"
    ]
    assert payload["context_id"].startswith("sha256:")


class _CountingKnowledgeBase(_MinimalKnowledgeBase):
    def __init__(self, *, version: str = "2.0.0") -> None:
        super().__init__(module_name="clinical_reporting", version=version)
        self.exports = 0
        self.examination_name = "gastroscopy"

    def export_core_concepts(self) -> JsonObject:
        self.exports += 1
        payload = super().export_core_concepts()
        payload["examination"] = [{"name": self.examination_name}]
        return payload


_GRAPH = "/knowledge-bases/{module_name}/{version}/graph"
_CONTEXT = (
    "/knowledge-bases/{module_name}/{version}/examinations/"
    "{examination_name}/reporting-context"
)


def test_http_graph_and_context_reuse_index_and_isolate_responses() -> None:
    kb = _CountingKnowledgeBase()
    loads = 0

    def load(module_name: str, *, version: str) -> _MinimalKnowledgeBase:
        nonlocal loads
        loads += 1
        return kb

    routes = _registered_routes(load)
    graph = routes.handlers[_GRAPH](None, kb.module_name, kb.version)
    original_id = graph["snapshot_id"]
    graph.clear()
    context = routes.handlers[_CONTEXT](None, kb.module_name, kb.version, "gastroscopy")
    assert context["graph_snapshot_id"] == original_id
    context.clear()
    assert (
        routes.handlers[_CONTEXT](None, kb.module_name, kb.version, "gastroscopy")[
            "graph_snapshot_id"
        ]
        == original_id
    )
    assert (
        routes.handlers[_GRAPH](None, kb.module_name, kb.version)["snapshot_id"]
        == original_id
    )
    assert kb.exports == 1
    assert loads == 4


def test_http_cache_replaces_source_and_never_masks_loader_failure() -> None:
    kb = _CountingKnowledgeBase()
    failure = False

    def load(module_name: str, *, version: str) -> _MinimalKnowledgeBase:
        if failure:
            raise HttpError(409, "Unavailable version")
        return kb

    route = _registered_routes(load).handlers[_GRAPH]
    first = route(None, kb.module_name, kb.version)
    kb = _CountingKnowledgeBase()
    kb.examination_name = "colonoscopy"
    second = route(None, kb.module_name, kb.version)
    assert first["snapshot_id"] != second["snapshot_id"]
    failure = True
    with pytest.raises(HttpError, match="Unavailable version"):
        route(None, kb.module_name, kb.version)
    failure = False
    assert route(None, kb.module_name, kb.version) == second
    assert kb.exports == 2  # A failed load evicts the formerly valid projection.
    kb = _CountingKnowledgeBase(version="wrong-version")
    with pytest.raises(HttpError, match="coherent graph snapshot"):
        route(None, kb.module_name, "2.0.0")


def test_http_cache_lru_bound_and_explicit_invalidation() -> None:
    from lx_dtypes.django.api.knowledge_base_graph_routes import (
        KnowledgeBaseGraphRouteCache,
    )

    sources = {v: _CountingKnowledgeBase(version=v) for v in ("1", "2", "3")}
    cache = KnowledgeBaseGraphRouteCache(max_entries=2)
    registry = _RouteRegistry()
    register_knowledge_base_graph_routes(
        registry,
        graph_cache=cache,
        load_module_kb=lambda module_name, *, version: sources[version],
    )
    route = registry.handlers[_GRAPH]
    for version in ("1", "2", "1", "3", "1", "2"):
        route(None, "clinical_reporting", version)
    assert [sources[v].exports for v in ("1", "2", "3")] == [1, 2, 1]
    sources["2"].examination_name = "colonoscopy"
    cache.clear()
    fresh = route(None, "clinical_reporting", "2")
    assert sources["2"].exports == 3
    assert (
        registry.handlers[_CONTEXT](None, "clinical_reporting", "2", "colonoscopy")[
            "graph_snapshot_id"
        ]
        == fresh["snapshot_id"]
    )
    with pytest.raises(HttpError) as error:
        registry.handlers[_CONTEXT](None, "clinical_reporting", "2", "gastroscopy")
    assert error.value.status_code == 404


def test_concurrent_http_cold_requests_compile_once() -> None:
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    kb = _CountingKnowledgeBase()
    route = _registered_routes(lambda *args, **kwargs: kb).handlers[_CONTEXT]
    barrier = Barrier(8)

    def request(_: int) -> dict[str, Any]:
        barrier.wait(timeout=10)
        return route(None, kb.module_name, kb.version, "gastroscopy")

    with ThreadPoolExecutor(max_workers=8) as pool:
        responses = list(pool.map(request, range(8)))
    assert all(response == responses[0] for response in responses)
    assert kb.exports == 1


def test_api_mutation_hook_invalidates_http_projection() -> None:
    from lx_dtypes.django.api import main as api_main

    kb = _CountingKnowledgeBase()
    registry = _RouteRegistry()
    register_knowledge_base_graph_routes(
        registry,
        graph_cache=api_main._graph_route_cache,
        load_module_kb=lambda *args, **kwargs: kb,
    )
    api_main._clear_kb_caches()
    try:
        route = registry.handlers[_GRAPH]
        original = route(None, kb.module_name, kb.version)
        kb.examination_name = "colonoscopy"
        api_main._clear_kb_caches()
        assert (
            route(None, kb.module_name, kb.version)["snapshot_id"]
            != original["snapshot_id"]
        )
        assert kb.exports == 2
    finally:
        api_main._clear_kb_caches()


@pytest.mark.parametrize("capacity", [0, -1])
def test_http_cache_rejects_nonpositive_capacity(capacity: int) -> None:
    from lx_dtypes.django.api.knowledge_base_graph_routes import (
        KnowledgeBaseGraphRouteCache,
    )

    with pytest.raises(ValueError, match="positive"):
        KnowledgeBaseGraphRouteCache(max_entries=capacity)


def test_invalidation_waits_for_compilation_and_prevents_retaining_old_build() -> None:
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event

    from lx_dtypes.django.api.knowledge_base_graph_routes import (
        KnowledgeBaseGraphRouteCache,
    )

    compiling = Event()
    release = Event()
    clearing = Event()
    cleared = Event()

    class BlockingSource(_CountingKnowledgeBase):
        def export_core_concepts(self) -> JsonObject:
            compiling.set()
            assert release.wait(timeout=10)
            return super().export_core_concepts()

    kb = BlockingSource()
    cache = KnowledgeBaseGraphRouteCache()
    registry = _RouteRegistry()
    register_knowledge_base_graph_routes(
        registry, graph_cache=cache, load_module_kb=lambda *args, **kwargs: kb
    )
    route = registry.handlers[_GRAPH]

    def clear() -> None:
        clearing.set()
        cache.clear()
        cleared.set()

    with ThreadPoolExecutor(max_workers=2) as pool:
        request = pool.submit(route, None, kb.module_name, kb.version)
        try:
            assert compiling.wait(timeout=10)
            invalidation = pool.submit(clear)
            assert clearing.wait(timeout=10)
            assert not cleared.is_set()
        finally:
            release.set()
        request.result(timeout=10)
        invalidation.result(timeout=10)
    kb.examination_name = "colonoscopy"
    registry.handlers[_CONTEXT](None, kb.module_name, kb.version, "colonoscopy")
    assert kb.exports == 2
