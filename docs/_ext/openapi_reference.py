"""Render the Django Ninja OpenAPI schema of ``lx_dtypes.django.api`` in Sphinx.

The schema is generated from the mounted ``NinjaAPI`` at build time, so the
reference cannot drift from the routes. Route docstrings become operation
descriptions in both the schema and this reference.

Directives:

``openapi-index``
    Summary table of every operation, linked to its detailed entry.
``openapi-endpoints <route module>``
    Detailed entries for the operations registered by one route module, for
    example ``findings_routes``.
``openapi-models <route module>``
    Autodoc entries for the API-specific request and response schemas used by
    that module's operations. Shared domain models (``lx_dtypes.models``) are
    linked rather than repeated, because the model reference documents them.

The schema is also written to ``_build/openapi/openapi.json`` before reading,
so pages can offer it with ``:download:``. Generated output stays in ``_build``.
"""

from __future__ import annotations

import json
import sys
from collections.abc import Iterator
from functools import lru_cache
from pathlib import Path
from typing import Any

from docutils import nodes
from docutils.statemachine import StringList
from pydantic import BaseModel
from sphinx.application import Sphinx
from sphinx.util.docutils import SphinxDirective
from sphinx.util.nodes import nested_parse_with_titles

_OPERATION_PREFIX = "lx_dtypes_django_api_"
_METHODS = ("get", "post", "put", "patch", "delete")
# Schemas defined here are documented on the HTTP API page itself.
_API_SCHEMA_MODULES = ("lx_dtypes.django.api.", "lx_dtypes.terminology.")

type Operation = tuple[str, str, dict[str, Any]]


@lru_cache(maxsize=1)
def openapi_schema() -> dict[str, Any]:
    """Return the OpenAPI schema of the shipped API (Django is set up in conf.py)."""
    from lx_dtypes.django.api.main import api

    return api.get_openapi_schema()  # type: ignore[attr-defined]


def _operations(module: str | None = None) -> Iterator[Operation]:
    """Yield ``(path, method, operation)`` in registration order."""
    for path, item in openapi_schema()["paths"].items():
        for method in _METHODS:
            operation = item.get(method)
            if operation is None:
                continue
            if module is None or _route_module(operation) == module:
                yield path, method, operation


def _route_module(operation: dict[str, Any]) -> str:
    """Return the defining module, e.g. ``findings_routes``, from the operation id."""
    operation_id: str = operation["operationId"]
    remainder = operation_id.removeprefix(_OPERATION_PREFIX)
    for candidate in _route_modules():
        if remainder.startswith(f"{candidate}_"):
            return candidate
    raise ValueError(f"Cannot determine the route module of {operation_id!r}.")


@lru_cache(maxsize=1)
def _route_modules() -> tuple[str, ...]:
    package = Path(sys.modules["lx_dtypes.django.api"].__file__ or "").parent
    # Longest first, so "report_template_routes" is not matched as "report".
    return tuple(
        sorted((path.stem for path in package.glob("*.py")), key=len, reverse=True)
    )


def _anchor(operation: dict[str, Any]) -> str:
    return "api-" + operation["operationId"].removeprefix(_OPERATION_PREFIX).replace(
        "_", "-"
    )


@lru_cache(maxsize=1)
def _schema_classes() -> dict[str, type[BaseModel]]:
    """Map OpenAPI component names to the unique Pydantic class of that name."""
    candidates: dict[str, set[type[BaseModel]]] = {}
    for module_name, module in list(sys.modules.items()):
        if not module_name.startswith("lx_dtypes.") or module is None:
            continue
        for value in vars(module).values():
            if isinstance(value, type) and issubclass(value, BaseModel):
                candidates.setdefault(value.__name__, set()).add(value)
    components = openapi_schema().get("components", {}).get("schemas", {})
    return {
        name: next(iter(classes))
        for name in components
        if len(classes := candidates.get(name, set())) == 1
    }


def _dotted(cls: type) -> str:
    return f"{cls.__module__}.{cls.__qualname__}"


def _ref_name(schema: dict[str, Any]) -> str | None:
    ref = schema.get("$ref")
    return ref.rsplit("/", 1)[-1] if isinstance(ref, str) else None


def _ref_role(name: str) -> str:
    cls = _schema_classes().get(name)
    return f":py:class:`~{_dotted(cls)}`" if cls else f"``{name}``"


def _type(schema: dict[str, Any]) -> str:
    """Format a JSON schema as a short inline type."""
    if name := _ref_name(schema):
        return _ref_role(name)
    for key in ("anyOf", "oneOf"):
        if key in schema:
            return " | ".join(_type(item) for item in schema[key])
    if "enum" in schema:
        return " | ".join(f"``{value!r}``" for value in schema["enum"])
    kind = schema.get("type")
    if kind == "array":
        return f"list[{_type(schema.get('items', {}))}]"
    if kind == "string" and schema.get("format") == "binary":
        return "file"
    if kind == "object":
        values = schema.get("additionalProperties")
        return f"dict[str, {_type(values)}]" if isinstance(values, dict) else "object"
    if kind == "null":
        return "``null``"
    if isinstance(kind, str):
        return kind + (f" ({schema['format']})" if "format" in schema else "")
    return "any"


def _referenced_components(value: object) -> Iterator[str]:
    """Yield every component name referenced anywhere inside ``value``."""
    if isinstance(value, dict):
        if name := _ref_name(value):
            yield name
        for item in value.values():
            yield from _referenced_components(item)
    elif isinstance(value, list):
        for item in value:
            yield from _referenced_components(item)


def _component_closure(roots: list[str]) -> list[str]:
    """Return ``roots`` and the components they reference, in first-seen order."""
    components = openapi_schema().get("components", {}).get("schemas", {})
    ordered: list[str] = []
    pending = list(roots)
    while pending:
        name = pending.pop(0)
        if name in ordered:
            continue
        ordered.append(name)
        pending.extend(_referenced_components(components.get(name, {})))
    return ordered


def _operation_lines(path: str, method: str, operation: dict[str, Any]) -> list[str]:
    title = f"``{method.upper()}`` {path}"
    lines = [f".. _{_anchor(operation)}:", "", title, "~" * len(title), ""]
    lines += [f"**{operation.get('summary', operation['operationId'])}**", ""]
    description = operation.get("description")
    lines += [*(description.splitlines() if description else []), ""]

    parameters = operation.get("parameters", [])
    if parameters:
        lines += [
            ".. list-table:: Parameters",
            "   :header-rows: 1",
            "   :widths: 25 12 43 20",
            "",
            "   * - Name",
            "     - In",
            "     - Type",
            "     - Required",
        ]
        for parameter in parameters:
            schema = parameter.get("schema", {})
            required = "yes" if parameter.get("required") else "no"
            if "default" in schema:
                required += f" (default ``{schema['default']!r}``)"
            lines += [
                f"   * - ``{parameter['name']}``",
                f"     - {parameter['in']}",
                f"     - {_type(schema)}",
                f"     - {required}",
            ]
        lines.append("")

    body = operation.get("requestBody")
    if body:
        for media_type, content in body.get("content", {}).items():
            lines += [
                f"**Request body** ({media_type}): {_type(content.get('schema', {}))}",
                "",
            ]

    for status, response in operation.get("responses", {}).items():
        content = response.get("content", {}).get("application/json")
        shape = _type(content["schema"]) if content else "JSON, schema not declared"
        lines += [f"**Response** ``{status}``: {shape}", ""]
    return lines


class OpenApiIndexDirective(SphinxDirective):
    """Summary table of every operation."""

    def run(self) -> list[nodes.Node]:
        lines = [
            ".. list-table::",
            "   :header-rows: 1",
            "   :widths: 10 55 35",
            "",
            "   * - Method",
            "     - Path",
            "     - Summary",
        ]
        for path, method, operation in _operations():
            lines += [
                f"   * - ``{method.upper()}``",
                f"     - :ref:`{path} <{_anchor(operation)}>`",
                f"     - {operation.get('summary', '')}",
            ]
        return _parse(self, lines)


class OpenApiEndpointsDirective(SphinxDirective):
    """Detailed entries for one route module's operations."""

    required_arguments = 1

    def run(self) -> list[nodes.Node]:
        lines: list[str] = []
        for path, method, operation in _operations(self.arguments[0]):
            lines += _operation_lines(path, method, operation)
        if not lines:
            raise self.error(f"No operations found for {self.arguments[0]!r}.")
        return _parse(self, lines, titles=True)


class OpenApiModelsDirective(SphinxDirective):
    """Autodoc entries for API-specific schemas used by one route module."""

    required_arguments = 1

    def run(self) -> list[nodes.Node]:
        # Per-document state: document each model once per page.
        documented = self.env.temp_data.setdefault("openapi_documented_models", set())
        assert isinstance(documented, set)
        roots = [
            name
            for _, _, operation in _operations(self.arguments[0])
            for name in _referenced_components(operation)
        ]
        lines: list[str] = []
        for name in _component_closure(roots):
            cls = _schema_classes().get(name)
            if cls is None or not cls.__module__.startswith(_API_SCHEMA_MODULES):
                continue
            dotted = _dotted(cls)
            if dotted in documented:
                continue
            documented.add(dotted)
            lines += [f".. autoclass:: {dotted}", "   :members:", ""]
        return _parse(self, lines) if lines else []


def _parse(
    directive: SphinxDirective, lines: list[str], *, titles: bool = False
) -> list[nodes.Node]:
    container = nodes.section() if titles else nodes.container()
    container.document = directive.state.document
    content = StringList(lines, source=directive.get_source_info()[0])
    if titles:
        nested_parse_with_titles(directive.state, content, container)
    else:
        directive.state.nested_parse(content, directive.content_offset, container)
    return list(container.children)


SCHEMA_DOWNLOAD = Path("_build/openapi/openapi.json")


def _write_schema(app: Sphinx) -> None:
    target = Path(app.srcdir) / SCHEMA_DOWNLOAD
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(openapi_schema(), indent=2) + "\n", encoding="utf-8")


def setup(app: Sphinx) -> dict[str, Any]:
    app.add_directive("openapi-index", OpenApiIndexDirective)
    app.add_directive("openapi-endpoints", OpenApiEndpointsDirective)
    app.add_directive("openapi-models", OpenApiModelsDirective)
    app.connect("builder-inited", _write_schema)
    return {"version": "1", "parallel_read_safe": True, "parallel_write_safe": True}
