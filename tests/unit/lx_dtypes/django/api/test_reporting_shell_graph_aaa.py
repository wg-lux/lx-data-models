from __future__ import annotations

from collections.abc import Callable
from typing import Any, ClassVar, TypeVar

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
    report_template: ClassVar[JsonObject] = {}
    findings_validator: ClassVar[JsonObject] = {}
    classification_validator: ClassVar[JsonObject] = {}
    intervention_validator: ClassVar[JsonObject] = {}
    unit_validator: ClassVar[JsonObject] = {}
    examination_validator: ClassVar[JsonObject] = {}

    def __init__(self, *, module_name: str, version: str) -> None:
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
    assert "colonoscopy" in str(error.value)


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
