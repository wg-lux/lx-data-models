#!/usr/bin/env python3
"""Check shared model inheritance and reviewed contract dependency exceptions.

This is a static architecture check: it never imports application or model code.
The canonical inventory is docs/model-boundaries.yml, not a second model schema.
"""

from __future__ import annotations

import argparse
import ast
from collections.abc import Iterator
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field

_RUNTIME_DEPENDENCIES = (
    "lx_dtypes.evaluation",
    "lx_dtypes.validation",
    "lx_dtypes.numeric_classification",
    "lx_dtypes.models.interface",
    "lx_dtypes.models.knowledge_base",
    "lx_dtypes.models.ledger",
    "lx_dtypes.terminology",
    "lx_dtypes.stats",
    "django",
    "ninja",
    "numpy",
    "pandas",
    "scipy",
    "torch",
    "cv2",
)


class ExtraException(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    path: str
    policy: Literal["allow", "ignore"]
    models: list[str] = Field(min_length=1)
    reason: str = Field(min_length=1)


class DependencyException(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    path: str
    dependencies: list[str] = Field(min_length=1)
    reason: str = Field(min_length=1)


class FrameworkAdapter(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    path: str
    base: str
    models: list[str] = Field(min_length=1)
    reason: str = Field(min_length=1)


class BoundaryInventory(BaseModel):
    # Explanatory metadata is retained alongside the checked inventories.
    model_config = ConfigDict(extra="allow", strict=True)
    version: Literal[1]
    extra_field_exceptions: list[ExtraException]
    contract_runtime_dependencies: list[DependencyException]
    framework_adapters: list[FrameworkAdapter]


def _runtime_imports(node: ast.AST) -> Iterator[ast.ImportFrom | ast.Import]:
    if isinstance(node, ast.If) and (
        isinstance(node.test, ast.Name)
        and node.test.id == "TYPE_CHECKING"
        or isinstance(node.test, ast.Attribute)
        and node.test.attr == "TYPE_CHECKING"
    ):
        for child in node.orelse:
            yield from _runtime_imports(child)
        return
    if isinstance(node, (ast.ImportFrom, ast.Import)):
        yield node
    for child in ast.iter_child_nodes(node):
        yield from _runtime_imports(child)


def inventory(
    root: Path,
) -> tuple[
    set[str], set[tuple[str, str, str]], set[tuple[str, str]], set[tuple[str, str, str]]
]:
    unshared: set[str] = set()
    extras: set[tuple[str, str, str]] = set()
    dependencies: set[tuple[str, str]] = set()
    frameworks: set[tuple[str, str, str]] = set()
    for path in sorted((root / "lx_dtypes").rglob("*.py")):
        relative = path.relative_to(root).as_posix()
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=relative)
        pydantic_bases = {
            alias.asname or alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module == "pydantic"
            for alias in node.names
            if alias.name in {"BaseModel", "RootModel"}
        }
        pydantic_modules = {
            alias.asname or alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
            if alias.name == "pydantic"
        }
        framework_bases = {
            alias.asname or alias.name: f"{node.module}.{alias.name}"
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module == "ninja"
            for alias in node.names
            if alias.name in {"Schema", "ModelSchema", "FilterSchema"}
        }
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            for base in node.bases:
                value = base.value if isinstance(base, ast.Subscript) else base
                direct = isinstance(value, ast.Name) and value.id in pydantic_bases
                qualified = (
                    isinstance(value, ast.Attribute)
                    and value.attr in {"BaseModel", "RootModel"}
                    and isinstance(value.value, ast.Name)
                    and value.value.id in pydantic_modules
                )
                if (direct or qualified) and relative != "lx_dtypes/models/model.py":
                    unshared.add(f"{relative}:{node.name}")
                if isinstance(value, ast.Name) and value.id in framework_bases:
                    frameworks.add((relative, node.name, framework_bases[value.id]))
            for item in node.body:
                if not (
                    isinstance(item, ast.Assign)
                    and any(
                        isinstance(target, ast.Name) and target.id == "model_config"
                        for target in item.targets
                    )
                ):
                    continue
                if isinstance(item.value, ast.Call):
                    options = [
                        (keyword.arg, keyword.value) for keyword in item.value.keywords
                    ]
                elif isinstance(item.value, ast.Dict):
                    options = [
                        (key.value, value)
                        for key, value in zip(
                            item.value.keys, item.value.values, strict=True
                        )
                        if isinstance(key, ast.Constant)
                    ]
                else:
                    continue
                for name, value in options:
                    if (
                        name == "extra"
                        and isinstance(value, ast.Constant)
                        and value.value in {"allow", "ignore"}
                    ):
                        extras.add((relative, node.name, str(value.value)))
        if not relative.startswith("lx_dtypes/models/contracts/"):
            continue
        package = relative.removesuffix(".py").replace("/", ".").rsplit(".", 1)[0]
        for node in _runtime_imports(tree):
            if isinstance(node, ast.ImportFrom):
                if node.level:
                    parts = package.split(".")
                    module = ".".join(
                        parts[: len(parts) - node.level + 1]
                        + ([node.module] if node.module else [])
                    )
                else:
                    module = node.module or ""
                modules = [module]
            else:
                modules = [alias.name for alias in node.names]
            for module in modules:
                if any(
                    module == prefix or module.startswith(prefix + ".")
                    for prefix in _RUNTIME_DEPENDENCIES
                ):
                    dependencies.add((relative, module))
    return unshared, extras, dependencies, frameworks


def check(root: Path, policy: BoundaryInventory) -> list[str]:
    unshared, extras, dependencies, frameworks = inventory(root)
    expected_extras = {
        (entry.path, model, entry.policy)
        for entry in policy.extra_field_exceptions
        for model in entry.models
    }
    expected_dependencies = {
        (entry.path, dependency)
        for entry in policy.contract_runtime_dependencies
        for dependency in entry.dependencies
    }
    expected_frameworks = {
        (entry.path, model, entry.base)
        for entry in policy.framework_adapters
        for model in entry.models
    }
    errors = [f"Model bypasses shared policy: {name}" for name in sorted(unshared)]
    for title, count, unique in (
        (
            "extra-field exception",
            sum(len(entry.models) for entry in policy.extra_field_exceptions),
            len(expected_extras),
        ),
        (
            "contract runtime dependency",
            sum(
                len(entry.dependencies)
                for entry in policy.contract_runtime_dependencies
            ),
            len(expected_dependencies),
        ),
        (
            "framework adapter",
            sum(len(entry.models) for entry in policy.framework_adapters),
            len(expected_frameworks),
        ),
    ):
        if count != unique:
            errors.append(f"Duplicate {title} in the reviewed inventory")
    for title, actual, expected in (
        ("extra-field exception", extras, expected_extras),
        ("contract runtime dependency", dependencies, expected_dependencies),
        ("framework adapter", frameworks, expected_frameworks),
    ):
        errors.extend(
            f"Unreviewed {title}: {item}" for item in sorted(actual - expected)
        )
        errors.extend(f"Stale {title}: {item}" for item in sorted(expected - actual))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--report",
        action="store_true",
        help="Print observed exceptions without changing the reviewed inventory",
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    if args.report:
        unshared, extras, dependencies, frameworks = inventory(root)
        print(
            yaml.safe_dump(
                {
                    "unshared_models": sorted(unshared),
                    "extra_field_exceptions": [list(item) for item in sorted(extras)],
                    "contract_runtime_dependencies": [
                        list(item) for item in sorted(dependencies)
                    ],
                    "framework_adapters": [list(item) for item in sorted(frameworks)],
                },
                sort_keys=False,
            )
        )
        return 0
    policy = BoundaryInventory.model_validate(
        yaml.safe_load((root / "docs/model-boundaries.yml").read_text(encoding="utf-8"))
    )
    errors = check(root, policy)
    for error in errors:
        print(error)
    if errors:
        return 1
    print(
        "Model boundaries: shared policies and reviewed dependency exceptions passed."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
