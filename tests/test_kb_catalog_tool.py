"""Maintainer workflow tests for ``scripts/kb_catalog.py`` on a synthetic git repository."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from lx_dtypes.knowledge_bases import knowledge_base_content_sha256
from lx_dtypes.models.interface.KnowledgeBaseResolver import (
    clear_knowledge_base_resolver_caches,
    load_knowledge_base,
)
from scripts import kb_catalog

BASE = "base_terms"
REPORT = "demo_report"


def _write_module(
    data_root: Path,
    name: str,
    *,
    unit: str,
    depends_on: tuple[str, ...] = (),
) -> Path:
    module_dir = data_root / "terminology" / name
    (module_dir / "data").mkdir(parents=True)
    depends = "".join(f"  - {item}\n" for item in depends_on)
    (module_dir / "config.yaml").write_text(
        f"name: {name}\n"
        "description: Synthetic catalog tool module\n"
        'version: "1.0.0"\n'
        "modules: []\n"
        + (f"depends_on:\n{depends}" if depends_on else "depends_on: []\n")
        + "data:\n  dirs:\n    - ./data\n",
        encoding="utf-8",
    )
    (module_dir / "data" / "units.yaml").write_text(
        f"- model: unit\n  name: {unit}\n  abbreviation: u\n", encoding="utf-8"
    )
    return module_dir


def _git(repo: Path, *args: str) -> None:
    subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "-c",
            "user.name=Catalog Test",
            "-c",
            "user.email=catalog-test@example.invalid",
            "-c",
            "commit.gpgsign=false",
            *args,
        ],
        check=True,
        capture_output=True,
    )


@pytest.fixture
def repo(tmp_path: Path) -> kb_catalog.Repository:
    root = tmp_path / "repo"
    data_root = root / "lx_dtypes" / "data"
    entries = []
    for name, unit, depends in (
        (BASE, "base_unit", ()),
        (REPORT, "report_unit", (BASE,)),
    ):
        module_dir = _write_module(data_root, name, unit=unit, depends_on=depends)
        entries.append(
            {
                "module_name": name,
                "version": "1.0.0",
                "package_kind": "terminology",
                "resource_root": f"data/terminology/{name}",
                "content_sha256": knowledge_base_content_sha256(module_dir),
                "default": True,
            }
        )
    (data_root / "catalog.json").write_text(
        json.dumps({"schema_version": 1, "knowledge_bases": entries}, indent=2) + "\n",
        encoding="utf-8",
    )
    repository = kb_catalog.Repository(root)
    repository.write_pins({})
    _git(root, "init", "-q")
    _git(root, "add", ".")
    _git(root, "commit", "-q", "-m", "Publish synthetic releases")
    return repository


@pytest.fixture(autouse=True)
def _clear_caches() -> None:
    clear_knowledge_base_resolver_caches()


def _status(repo: kb_catalog.Repository) -> dict[str, list[kb_catalog.Problem]]:
    return {
        report.identity: report.problems for report in kb_catalog.collect_status(repo)
    }


def _module_dir(repo: kb_catalog.Repository, name: str) -> Path:
    return repo.root / "lx_dtypes" / "data" / "terminology" / name


def _edit_report(repo: kb_catalog.Repository) -> None:
    units = _module_dir(repo, REPORT) / "data" / "units.yaml"
    units.write_text(
        units.read_text(encoding="utf-8")
        + "- model: unit\n  name: added_unit\n  abbreviation: a\n",
        encoding="utf-8",
    )


def test_status_is_clean_for_a_consistent_catalog(
    repo: kb_catalog.Repository, capsys: pytest.CaptureFixture[str]
) -> None:
    assert kb_catalog.main(["--repo-root", str(repo.root), "status"]) == 0
    assert "0 failure(s)" in capsys.readouterr().out


def test_status_explains_an_in_place_edit_of_a_committed_release(
    repo: kb_catalog.Repository, capsys: pytest.CaptureFixture[str]
) -> None:
    _edit_report(repo)

    assert kb_catalog.main(["--repo-root", str(repo.root), "status"]) == 1

    output = capsys.readouterr().out
    assert f"FAIL  {REPORT}@1.0.0" in output
    assert "may have shipped" in output
    assert f"new-version {REPORT} <next-version>" in output
    assert f"git restore lx_dtypes/data/terminology/{REPORT}" in output


def test_new_version_retains_published_bytes_and_keeps_edits(
    repo: kb_catalog.Repository,
) -> None:
    published_digest = knowledge_base_content_sha256(_module_dir(repo, REPORT))
    _edit_report(repo)

    plan = kb_catalog.new_version(repo, REPORT, "1.1.0")

    retained = repo.root / "lx_dtypes/data/terminology/versions" / REPORT / "1.0.0"
    assert plan.copied_dirs == (BASE, REPORT)
    assert knowledge_base_content_sha256(retained / REPORT) == published_digest
    assert (retained / BASE / "config.yaml").is_file()
    assert 'version: "1.1.0"' in (_module_dir(repo, REPORT) / "config.yaml").read_text(
        encoding="utf-8"
    )

    _payload, entries = repo.read_catalog()
    by_identity = {kb_catalog.identity(entry): entry for entry in entries}
    assert by_identity[f"{REPORT}@1.1.0"]["default"] is True
    assert by_identity[f"{REPORT}@1.0.0"]["default"] is False
    assert by_identity[f"{REPORT}@1.0.0"]["resource_root"] == (
        f"data/terminology/versions/{REPORT}/1.0.0/{REPORT}"
    )
    assert repo.read_pins() == {
        f"{REPORT}@1.0.0": knowledge_base_content_sha256(retained)
    }
    assert all(not problems for problems in _status(repo).values())

    old = load_knowledge_base(REPORT, version="1.0.0", input_dirs=[retained])
    new = load_knowledge_base(
        REPORT, version="1.1.0", input_dirs=[repo.root / "lx_dtypes" / "data"]
    )
    assert "added_unit" not in old.unit
    assert "added_unit" in new.unit


def test_new_version_dry_run_writes_nothing(repo: kb_catalog.Repository) -> None:
    catalog_before = repo.catalog_path.read_bytes()

    plan = kb_catalog.new_version(repo, REPORT, "1.1.0", dry_run=True)

    assert plan.new_version == "1.1.0"
    assert repo.catalog_path.read_bytes() == catalog_before
    assert not (repo.root / "lx_dtypes/data/terminology/versions").exists()


def test_new_version_refuses_when_the_edit_was_already_committed(
    repo: kb_catalog.Repository,
) -> None:
    _edit_report(repo)
    _git(repo.root, "commit", "-q", "-am", "Edit published release in place")

    with pytest.raises(kb_catalog.CatalogToolError, match="--from-ref <commit>"):
        kb_catalog.new_version(repo, REPORT, "1.1.0")

    kb_catalog.new_version(repo, REPORT, "1.1.0", from_ref="HEAD~1")
    assert repo.read_pins().keys() == {f"{REPORT}@1.0.0"}


def test_new_version_rejects_an_existing_version(repo: kb_catalog.Repository) -> None:
    with pytest.raises(kb_catalog.CatalogToolError, match="never published"):
        kb_catalog.new_version(repo, REPORT, "1.0.0")


def test_refresh_digest_protects_committed_releases(
    repo: kb_catalog.Repository,
) -> None:
    _edit_report(repo)

    with pytest.raises(kb_catalog.CatalogToolError, match="new-version"):
        kb_catalog.refresh_digest(repo, REPORT)

    release, old, new = kb_catalog.refresh_digest(repo, REPORT, allow_committed=True)
    assert release == f"{REPORT}@1.0.0"
    assert old != new


def test_refresh_digest_updates_an_unreleased_version(
    repo: kb_catalog.Repository,
) -> None:
    kb_catalog.new_version(repo, REPORT, "1.1.0")
    _edit_report(repo)
    assert any(
        problem.severity == "WARN" for problem in _status(repo)[f"{REPORT}@1.1.0"]
    )

    kb_catalog.refresh_digest(repo, REPORT)

    assert all(not problems for problems in _status(repo).values())


def test_status_detects_edits_to_snapshotted_dependencies(
    repo: kb_catalog.Repository,
) -> None:
    kb_catalog.new_version(repo, REPORT, "1.1.0")
    dependency_units = (
        repo.root
        / "lx_dtypes/data/terminology/versions"
        / REPORT
        / "1.0.0"
        / BASE
        / "data"
        / "units.yaml"
    )
    dependency_units.write_text("[]\n", encoding="utf-8")

    problems = _status(repo)[f"{REPORT}@1.0.0"]

    assert [problem.severity for problem in problems] == ["FAIL"]
    assert "differs from its pin" in problems[0].message
    assert f"git restore lx_dtypes/data/terminology/versions/{REPORT}/1.0.0" in (
        problems[0].fix
    )


def test_status_flags_a_removed_committed_release(
    repo: kb_catalog.Repository,
) -> None:
    payload, entries = repo.read_catalog()
    repo.write_catalog(
        payload, [entry for entry in entries if entry["module_name"] != BASE]
    )

    problems = _status(repo)[f"{BASE}@1.0.0"]

    assert problems[0].severity == "FAIL"
    assert "Hosts may have pinned it" in problems[0].message


def test_status_redirects_a_hand_edited_version_to_new_version(
    repo: kb_catalog.Repository,
) -> None:
    config = _module_dir(repo, REPORT) / "config.yaml"
    config.write_text(
        config.read_text(encoding="utf-8").replace('"1.0.0"', '"2.0.0"'),
        encoding="utf-8",
    )

    fixes = " ".join(problem.fix for problem in _status(repo)[f"{REPORT}@1.0.0"])

    assert f"new-version {REPORT} 2.0.0" in fixes
