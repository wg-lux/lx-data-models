from __future__ import annotations

from typing import Any, Callable, Dict, Protocol, TypeVar, cast

from ninja.errors import HttpError  # type: ignore[import-untyped]

from lx_dtypes.models.contracts.knowledge_base import (
    KnowledgeBaseContract,
    KnowledgeBaseIdentity,
)
from lx_dtypes.models.contracts.knowledge_base_graph import (
    ExaminationReportingContext,
    KnowledgeBaseGraphSnapshot,
    build_examination_reporting_context,
    build_knowledge_base_graph_snapshot,
)

from .request_types import BaseRequest

F = TypeVar("F", bound=Callable[..., Any])


class _RouteDecorator(Protocol):
    def __call__(self, func: F, /) -> F: ...


class _TypedApi(Protocol):
    def get(self, path: str, /) -> _RouteDecorator: ...


def register_knowledge_base_graph_routes(
    api: _TypedApi,
    *,
    load_module_kb: Callable[..., KnowledgeBaseContract],
) -> None:
    def load_snapshot(module_name: str, version: str) -> KnowledgeBaseGraphSnapshot:
        identity = KnowledgeBaseIdentity(
            knowledge_base_module=module_name,
            knowledge_base_version=version,
        )
        kb = load_module_kb(module_name, version=version)
        try:
            return build_knowledge_base_graph_snapshot(
                cast(Any, kb),
                identity=identity,
            )
        except ValueError as exc:
            raise HttpError(
                409,
                "The resolved knowledge base cannot produce a coherent graph "
                f"snapshot: {exc}",
            ) from exc

    @api.get("/knowledge-bases/{module_name}/{version}/graph")
    def knowledge_base_graph(
        request: BaseRequest,
        module_name: str,
        version: str,
    ) -> Dict[str, Any]:
        """Return one deterministic, fully resolved terminology graph snapshot."""

        del request
        return load_snapshot(module_name, version).model_dump(mode="json")

    @api.get(
        "/knowledge-bases/{module_name}/{version}/examinations/"
        "{examination_name}/reporting-context"
    )
    def examination_reporting_context(
        request: BaseRequest,
        module_name: str,
        version: str,
        examination_name: str,
    ) -> Dict[str, Any]:
        """Return the closed terminology/template projection for one examination."""

        del request
        snapshot = load_snapshot(module_name, version)
        try:
            context: ExaminationReportingContext = build_examination_reporting_context(
                snapshot,
                examination_name=examination_name,
            )
        except KeyError as exc:
            raise HttpError(
                404,
                f"Examination '{examination_name}' is not defined by "
                f"{module_name}@{version}.",
            ) from exc
        return context.model_dump(mode="json")


__all__ = ["register_knowledge_base_graph_routes"]
