from __future__ import annotations

from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass
from threading import RLock
from typing import Any, Protocol, TypeVar, cast

from ninja.errors import HttpError  # type: ignore[import-untyped]

from lx_dtypes.models.contracts.knowledge_base import (
    KnowledgeBaseContract,
    KnowledgeBaseIdentity,
)
from lx_dtypes.models.contracts.knowledge_base_graph import (
    ExaminationReportingContext,
    KnowledgeBaseGraphResolver,
    KnowledgeBaseGraphSnapshot,
    build_knowledge_base_graph_snapshot,
)

from .request_types import BaseRequest

F = TypeVar("F", bound=Callable[..., Any])


class _RouteDecorator(Protocol):
    def __call__(self, func: F, /) -> F: ...


class _TypedApi(Protocol):
    def get(self, path: str, /) -> _RouteDecorator: ...


@dataclass(frozen=True)
class _ResolvedGraph:
    source: KnowledgeBaseContract
    snapshot: KnowledgeBaseGraphSnapshot
    resolver: KnowledgeBaseGraphResolver


class KnowledgeBaseGraphRouteCache:
    """Bounded process-local projections; hosts must clear after in-place edits."""

    def __init__(self, *, max_entries: int = 8) -> None:
        if isinstance(max_entries, bool) or not isinstance(max_entries, int):
            raise TypeError("max_entries must be an integer")
        if max_entries < 1:
            raise ValueError("max_entries must be positive")
        self._max_entries = max_entries
        self._entries: OrderedDict[tuple[str, str], _ResolvedGraph] = OrderedDict()
        self._lock = RLock()

    def clear(self) -> None:
        """Invalidate retained projections, waiting for any current compilation."""
        with self._lock:
            self._entries.clear()

    def _resolve(
        self,
        module_name: str,
        version: str,
        load_module_kb: Callable[..., KnowledgeBaseContract],
    ) -> _ResolvedGraph:
        # Serialize loading/compilation with invalidation. A failed refresh must
        # never fall back to a previously valid projection of the same identity.
        with self._lock:
            key = (module_name, version)
            try:
                identity = KnowledgeBaseIdentity(
                    knowledge_base_module=module_name,
                    knowledge_base_version=version,
                )
                kb = load_module_kb(module_name, version=version)
                cached = self._entries.get(key)
                if cached is not None and cached.source is kb:
                    self._entries.move_to_end(key)
                    return cached
                snapshot = build_knowledge_base_graph_snapshot(
                    cast(Any, kb), identity=identity
                )
                resolved = _ResolvedGraph(
                    kb, snapshot, KnowledgeBaseGraphResolver(snapshot)
                )
            except Exception:
                self._entries.pop(key, None)
                raise
            self._entries[key] = resolved
            self._entries.move_to_end(key)
            while len(self._entries) > self._max_entries:
                self._entries.popitem(last=False)
            return resolved


def register_knowledge_base_graph_routes(
    api: _TypedApi,
    *,
    load_module_kb: Callable[..., KnowledgeBaseContract],
    graph_cache: KnowledgeBaseGraphRouteCache | None = None,
) -> None:
    cache = graph_cache if graph_cache is not None else KnowledgeBaseGraphRouteCache()

    def load_graph(module_name: str, version: str) -> _ResolvedGraph:
        try:
            return cache._resolve(module_name, version, load_module_kb)
        except ValueError as exc:
            raise HttpError(
                409,
                "The resolved knowledge base cannot produce a coherent graph snapshot.",
            ) from exc

    @api.get("/knowledge-bases/{module_name}/{version}/graph")
    def knowledge_base_graph(
        request: BaseRequest,
        module_name: str,
        version: str,
    ) -> dict[str, Any]:
        """Return one deterministic, fully resolved terminology graph snapshot."""

        del request
        return load_graph(module_name, version).snapshot.model_dump(mode="json")

    @api.get(
        "/knowledge-bases/{module_name}/{version}/examinations/"
        "{examination_name}/reporting-context"
    )
    def examination_reporting_context(
        request: BaseRequest,
        module_name: str,
        version: str,
        examination_name: str,
    ) -> dict[str, Any]:
        """Return the closed terminology/template projection for one examination."""

        del request
        graph = load_graph(module_name, version)
        try:
            context: ExaminationReportingContext = graph.resolver.reporting_context(
                examination_name
            )
        except KeyError as exc:
            raise HttpError(
                404,
                "The requested examination is unknown to this knowledge base.",
            ) from exc
        except ValueError as exc:
            raise HttpError(
                409, "The knowledge base cannot produce a coherent reporting context."
            ) from exc
        return context.model_dump(mode="json")


__all__ = ["KnowledgeBaseGraphRouteCache", "register_knowledge_base_graph_routes"]
