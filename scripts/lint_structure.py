#!/usr/bin/env python3
"""Validate repository context manifests without importing application code."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path
from typing import Annotated, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError

Text = Annotated[str, Field(min_length=1, pattern=r"\S")]


class Record(BaseModel):
    """Strict common fields; retain domain-specific metadata."""

    model_config = ConfigDict(strict=True, extra="allow")


class Entrypoint(Record):
    name: Text
    file: Text
    purpose: Text


class Submodule(Record):
    name: Text
    path: Text
    manifest: Text
    summary: Text


class Contract(Record):
    name: Text
    doc: Text


class Dependencies(Record):
    internal: list[Text]
    external: list[Text]


class Verification(Record):
    directory: Text
    command: Text


class Manifest(Record):
    version: Literal[1]
    tier: Literal["root", "domain", "service", "package", "tool"]
    path: Text
    parent: Text | None
    summary: Text
    responsibilities: Annotated[list[Text], Field(min_length=1)]
    boundaries: list[Text]
    entrypoints: list[Entrypoint]
    dependencies: Dependencies
    submodules: list[Submodule]
    contracts: list[Contract]
    tests: Verification
    files: list[Text] = Field(default_factory=list)


def discover_manifests(root: Path) -> list[Path]:
    """Include new manifests before staging, but never traverse ignored trees."""
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    return sorted(
        {
            root / name
            for name in result.stdout.decode().split("\0")
            if name and Path(name).name == "structure.yml"
        }
    )


def validate_structure(root: Path) -> list[str]:
    """Return deterministic schema, reference, and graph diagnostics."""
    root = root.resolve()
    errors: list[str] = []
    manifests: dict[Path, Manifest] = {}

    def reference(base: Path, value: str, kind: str = "any") -> Path:
        target = (base / value).resolve()
        if Path(value).is_absolute() or not target.is_relative_to(root):
            raise ValueError(
                f"reference must stay relative and inside repository: {value}"
            )
        exists = (
            target.is_file()
            if kind == "file"
            else (target.is_dir() if kind == "directory" else target.exists())
        )
        if not exists:
            raise ValueError(f"missing {kind} reference: {value}")
        return target

    try:
        paths = discover_manifests(root)
    except (OSError, subprocess.CalledProcessError) as exc:
        return [f"cannot discover manifests with git ls-files: {exc}"]
    for path in paths:
        label = path.relative_to(root).as_posix()
        try:
            reference(root, label, "file")
            data: object = yaml.safe_load(path.read_text(encoding="utf-8"))
            manifest = Manifest.model_validate(data)
            # Literal[1] also accepts True and 1.0; version is an integer contract.
            if not isinstance(data, dict) or type(data.get("version")) is not int:
                raise ValueError("version must be integer 1")
            manifests[path.resolve()] = manifest
            directory = reference(root, manifest.path, "directory")
            if directory != path.parent.resolve():
                raise ValueError("path does not match manifest directory")
            if (manifest.tier == "root") != (path == root / "structure.yml"):
                raise ValueError("only ./structure.yml may have tier root")
            for entry in manifest.entrypoints:
                reference(path.parent, entry.file, "file")
            for value in manifest.files + manifest.dependencies.internal:
                reference(path.parent, value)
            for contract in manifest.contracts:
                reference(path.parent, contract.doc, "file")
            reference(path.parent, manifest.tests.directory, "directory")
        except (
            OSError,
            UnicodeError,
            yaml.YAMLError,
            ValidationError,
            ValueError,
        ) as exc:
            errors.append(f"{label}: {exc}")

    root_manifest = root / "structure.yml"
    if root_manifest not in manifests:
        errors.append("structure.yml: missing or invalid root manifest")
    incoming: dict[Path, list[Path]] = {path: [] for path in manifests}
    edges: dict[Path, list[Path]] = {path: [] for path in manifests}
    for path, manifest in manifests.items():
        label = path.relative_to(root).as_posix()
        try:
            if path == root_manifest:
                if manifest.parent is not None:
                    raise ValueError("root parent must be null")
            elif manifest.parent is None:
                raise ValueError("child requires a parent manifest")
            else:
                parent = reference(path.parent, manifest.parent, "file")
                if parent not in manifests:
                    raise ValueError("parent is not a discovered valid manifest")
        except ValueError as exc:
            errors.append(f"{label}: parent: {exc}")
        for child in manifest.submodules:
            try:
                directory = reference(path.parent, child.path, "directory")
                target = reference(path.parent, child.manifest, "file")
                if directory == path.parent or not directory.is_relative_to(
                    path.parent
                ):
                    raise ValueError(
                        f"submodule {child.name} must be a descendant directory"
                    )
                if target.parent != directory or target not in manifests:
                    raise ValueError(
                        f"submodule {child.name} requires its own valid structure.yml"
                    )
                incoming[target].append(path)
                edges[path].append(target)
                parent_value = manifests[target].parent
                if (
                    parent_value is None
                    or reference(target.parent, parent_value, "file") != path
                ):
                    raise ValueError(
                        f"submodule {child.name}: parent does not match caller"
                    )
            except ValueError as exc:
                errors.append(f"{label}: {exc}")

    reached: set[Path] = set()
    pending = [root_manifest]
    while pending:
        path = pending.pop()
        if path not in reached:
            reached.add(path)
            pending.extend(edges.get(path, []))
    for path in manifests:
        if path == root_manifest:
            continue
        label = path.relative_to(root).as_posix()
        if len(incoming[path]) != 1:
            errors.append(
                f"{label}: expected exactly one parent link, got {len(incoming[path])}"
            )
        if path not in reached:
            errors.append(f"{label}: unreachable from root manifest")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[1]
    )
    args = parser.parse_args()
    errors = validate_structure(args.root)
    if errors:
        print("\n".join(errors))
        return 1
    print("Structure manifests: schema, references, and root reachability passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
