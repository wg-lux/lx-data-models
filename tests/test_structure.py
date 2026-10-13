"""Context validation uses synthetic Git trees and never loads runtime models."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from scripts.lint_structure import (
    Dependencies,
    Entrypoint,
    Manifest,
    Submodule,
    Verification,
    discover_manifests,
    validate_structure,
)


def write_manifest(directory: Path, **changes: object) -> None:
    data = Manifest(
        version=1,
        tier="root",
        path=".",
        parent=None,
        summary="Synthetic repository",
        responsibilities=["Validate context"],
        boundaries=["No runtime effects"],
        entrypoints=[Entrypoint(name="entry", file="entry.py", purpose="Example")],
        dependencies=Dependencies(internal=[], external=["Python"]),
        submodules=[],
        contracts=[],
        tests=Verification(directory=".", command="pytest"),
    ).model_dump()
    data.update(changes)
    directory.joinpath("structure.yml").write_text(yaml.safe_dump(data))


@pytest.fixture
def tree(tmp_path: Path) -> Path:
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    tmp_path.joinpath("entry.py").touch()
    child = tmp_path / "domain"
    child.mkdir()
    child.joinpath("entry.py").touch()
    write_manifest(child, tier="domain", path="domain", parent="../structure.yml")
    write_manifest(
        tmp_path,
        submodules=[
            Submodule(
                name="domain",
                path="domain",
                manifest="domain/structure.yml",
                summary="Example domain",
            ).model_dump()
        ],
    )
    return tmp_path


def test_valid_tree_preserves_custom_metadata(tree: Path) -> None:
    write_manifest(
        tree / "domain",
        tier="domain",
        path="domain",
        parent="../structure.yml",
        owner="Maintainers",
        files=["entry.py"],
    )
    assert validate_structure(tree) == []
    manifest = Manifest.model_validate(
        yaml.safe_load((tree / "domain/structure.yml").read_text())
    )
    assert manifest.model_extra == {"owner": "Maintainers"}


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"version": 2}, "version"),
        ({"version": True}, "version must be integer"),
        ({"version": 1.0}, "version must be integer"),
        ({"tier": "unknown"}, "tier"),
        ({"summary": " "}, "summary"),
        ({"responsibilities": []}, "responsibilities"),
        ({"parent": "entry.py"}, "root parent must be null"),
        ({"path": "domain"}, "path does not match"),
        (
            {
                "entrypoints": [
                    {"name": "broken", "file": "missing.py", "purpose": "Example"}
                ]
            },
            "missing file reference",
        ),
        (
            {
                "entrypoints": [
                    {"name": "directory", "file": "domain", "purpose": "Example"}
                ]
            },
            "missing file reference",
        ),
        ({"files": ["missing"]}, "missing any reference"),
        (
            {"contracts": [{"name": "missing", "doc": "absent.md"}]},
            "missing file reference",
        ),
        (
            {"dependencies": {"internal": ["absent"], "external": []}},
            "missing any reference",
        ),
        (
            {"tests": {"directory": "absent", "command": "pytest"}},
            "missing directory reference",
        ),
        (
            {
                "submodules": [
                    {
                        "name": "domain",
                        "path": "domain",
                        "manifest": "domain/missing.yml",
                        "summary": "Example",
                    }
                ]
            },
            "missing file reference",
        ),
        (
            {
                "submodules": [
                    {
                        "name": "domain",
                        "path": "absent",
                        "manifest": "domain/structure.yml",
                        "summary": "Example",
                    }
                ]
            },
            "missing directory reference",
        ),
        (
            {
                "submodules": [
                    {
                        "name": "domain",
                        "path": "domain",
                        "manifest": "entry.py",
                        "summary": "Example",
                    }
                ]
            },
            "requires its own valid structure.yml",
        ),
        (
            {
                "submodules": [
                    {
                        "name": "self",
                        "path": ".",
                        "manifest": "structure.yml",
                        "summary": "Example",
                    }
                ]
            },
            "descendant directory",
        ),
        ({"files": ["../outside"]}, "inside repository"),
    ],
)
def test_invalid_schema_and_references(
    tree: Path, changes: dict[str, object], message: str
) -> None:
    write_manifest(tree, **changes)
    assert any(message in error for error in validate_structure(tree))


@pytest.mark.parametrize("parent", [None, "missing.yml", "entry.py", "structure.yml"])
def test_missing_or_inconsistent_parent(tree: Path, parent: str | None) -> None:
    write_manifest(tree / "domain", tier="domain", path="domain", parent=parent)
    errors = validate_structure(tree)
    assert errors
    assert any("parent" in error for error in errors)


def test_orphan_and_duplicate_links(tree: Path) -> None:
    write_manifest(tree)
    assert any("unreachable" in error for error in validate_structure(tree))
    child = Submodule(
        name="domain", path="domain", manifest="domain/structure.yml", summary="Example"
    ).model_dump()
    write_manifest(tree, submodules=[child, child])
    assert any("got 2" in error for error in validate_structure(tree))


def test_git_discovery_ignores_artifacts_and_finds_unstaged_manifests(
    tree: Path,
) -> None:
    tree.joinpath(".gitignore").write_text(".venv/\nnode_modules/\ndocs/_build/\n")
    for ignored in (".venv", "node_modules", "docs/_build"):
        directory = tree / ignored
        directory.mkdir(parents=True)
        directory.joinpath("structure.yml").write_text("invalid: [")
    assert discover_manifests(tree) == [
        tree / "domain/structure.yml",
        tree / "structure.yml",
    ]
    assert validate_structure(tree) == []
    subprocess.run(["git", "add", "structure.yml"], cwd=tree, check=True)
    tree.joinpath("structure.yml").unlink()
    assert any("missing file reference" in error for error in validate_structure(tree))


def test_absolute_and_symlink_escape(tree: Path, tmp_path: Path) -> None:
    write_manifest(tree, files=[str(tree / "entry.py")])
    assert any("relative" in error for error in validate_structure(tree))
    outside = tmp_path.parent / f"{tmp_path.name}-outside"
    outside.mkdir()
    tree.joinpath("escape").symlink_to(outside, target_is_directory=True)
    write_manifest(tree, files=["escape"])
    assert any("inside repository" in error for error in validate_structure(tree))


@pytest.mark.parametrize(
    "content", ["summary: [", "- not a mapping", "summary: incomplete"]
)
def test_malformed_manifest(tree: Path, content: str) -> None:
    tree.joinpath("structure.yml").write_text(content)
    assert validate_structure(tree)


def test_cli_and_missing_root(tree: Path) -> None:
    script = Path(__file__).resolve().parents[1] / "scripts/lint_structure.py"
    result = subprocess.run(
        [sys.executable, str(script), "--root", str(tree)],
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    tree.joinpath("structure.yml").unlink()
    result = subprocess.run(
        [sys.executable, str(script), "--root", str(tree)],
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.returncode == 1
    assert "missing or invalid root" in result.stdout


def test_repository_structure() -> None:
    """The standard pytest lane also rejects drift in the actual repository."""
    assert validate_structure(Path(__file__).resolve().parents[1]) == []
