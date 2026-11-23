"""The OpenAPI schema is the source of the HTTP API reference in docs/api/http.rst."""

from __future__ import annotations

from typing import Any

from lx_dtypes.django.api import main as api_main


def _operations() -> list[tuple[str, str, dict[str, Any]]]:
    schema = api_main.api.get_openapi_schema()  # type: ignore[attr-defined]
    return [
        (path, method, operation)
        for path, item in schema["paths"].items()
        for method, operation in item.items()
    ]


def test_every_operation_has_a_description() -> None:
    # Ninja uses the route function's docstring as the description.
    undocumented = [
        f"{method.upper()} {path}"
        for path, method, operation in _operations()
        if not str(operation.get("description", "")).strip()
    ]
    assert undocumented == []


def test_protected_operations_document_their_authentication() -> None:
    # Every description states who may call the route.
    missing = [
        f"{method.upper()} {path}"
        for path, method, operation in _operations()
        if "authentication" not in str(operation.get("description", "")).lower()
    ]
    assert missing == []
