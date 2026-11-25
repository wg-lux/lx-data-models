#!/usr/bin/env python3
"""Maintain the packaged knowledge-base catalog without breaking published releases.

Published ``module@version`` releases are immutable: hosts pin their exact bytes.
This tool diagnoses the catalog and performs the two edits maintainers need:

``status``
    Check every catalog release against its files, the committed catalog, the
    retained-release pins and the retained layout. Prints a fix for each problem.
``new-version MODULE NEW_VERSION``
    Retain the committed bytes of the current default release (and the
    dependency modules it loads) under ``data/terminology/versions/``, bump the
    live ``config.yaml`` to ``NEW_VERSION`` and update the catalog and pins.
    Working-tree edits stay in the live directory and become the new version.
``refresh-digest MODULE``
    Recompute the catalog digest of an *unreleased* default release after edits.

Run from the repository root::

    uv run python scripts/kb_catalog.py status
"""

from __future__ import annotations

import argparse
import io
import json
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import warnings
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Literal

import yaml

from lx_dtypes.knowledge_bases import (
    PackagedKnowledgeBaseCatalog,
    knowledge_base_content_sha256,
)
from lx_dtypes.models.interface.data_roots import module_search_root
from lx_dtypes.models.interface.DataLoader import DataLoader

REPO_ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = PurePosixPath("lx_dtypes/data/catalog.json")
VERSIONS_PATH = PurePosixPath("lx_dtypes/data/terminology/versions")
PINS_PATH = PurePosixPath("tests/fixtures/lx_dtypes/retained_release_bundles.json")
RELEASE_GUIDE = "docs/guides/terminology-releases.md"
TOOL = "uv run python scripts/kb_catalog.py"
VERSION_LINE_RE = r"(?m)^(version:[ \t]*)(['\"]?){old}\2([ \t]*(?:#.*)?)$"

CatalogEntry = dict[str, object]
Severity = Literal["FAIL", "WARN"]


class CatalogToolError(RuntimeError):
    """A refused maintenance action; the message explains how to proceed."""


@dataclass(frozen=True)
class Problem:
    severity: Severity
    message: str
    fix: str


@dataclass
class ReleaseReport:
    identity: str
    role: str
    problems: list[Problem] = field(default_factory=list)

    def add(self, severity: Severity, message: str, fix: str) -> None:
        self.problems.append(Problem(severity, message, fix))


# --------------------------------------------------------------------------- #
# Repository files
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class Repository:
    root: Path

    @property
    def catalog_path(self) -> Path:
        return self.root / CATALOG_PATH

    @property
    def pins_path(self) -> Path:
        return self.root / PINS_PATH

    def module_dir(self, entry: CatalogEntry) -> Path:
        return self.root / "lx_dtypes" / str(entry["resource_root"])

    def repo_path(self, path: Path) -> str:
        return path.relative_to(self.root).as_posix()

    def read_catalog(self) -> tuple[dict[str, object], list[CatalogEntry]]:
        return _parse_catalog(self.catalog_path.read_text(encoding="utf-8"))

    def write_catalog(
        self, payload: dict[str, object], entries: list[CatalogEntry]
    ) -> None:
        updated = {**payload, "knowledge_bases": entries}
        text = json.dumps(updated, indent=2) + "\n"
        _validate_catalog_text(text)
        self.catalog_path.write_text(text, encoding="utf-8")

    def committed_catalog(self, ref: str = "HEAD") -> list[CatalogEntry] | None:
        text = _git_show(self.root, ref, CATALOG_PATH)
        if text is None:
            return None
        return _parse_catalog(text)[1]

    def read_pins(self) -> dict[str, str]:
        if not self.pins_path.is_file():
            return {}
        payload = json.loads(self.pins_path.read_text(encoding="utf-8"))
        pins = payload.get("retained_releases") if isinstance(payload, dict) else None
        if not isinstance(pins, dict):
            raise CatalogToolError(
                f"{PINS_PATH} must be an object with a `retained_releases` object."
            )
        return {str(key): str(value) for key, value in pins.items()}

    def write_pins(self, pins: dict[str, str]) -> None:
        payload = {
            "schema_version": 1,
            "description": (
                "Digest of every YAML file in each retained release bundle "
                "(the module and its snapshotted dependencies). Append-only: "
                f"never edit an existing value. Maintained by `{TOOL} new-version`."
            ),
            "retained_releases": dict(sorted(pins.items())),
        }
        self.pins_path.parent.mkdir(parents=True, exist_ok=True)
        self.pins_path.write_text(json.dumps(payload, indent=2) + "\n", "utf-8")


def _parse_catalog(text: str) -> tuple[dict[str, object], list[CatalogEntry]]:
    _validate_catalog_text(text)
    payload = json.loads(text)
    entries = payload["knowledge_bases"]
    return payload, [dict(entry) for entry in entries]


def _validate_catalog_text(text: str) -> None:
    try:
        PackagedKnowledgeBaseCatalog.model_validate_json(text)
    except ValueError as exc:
        raise CatalogToolError(f"{CATALOG_PATH} is invalid:\n{exc}") from exc


def _git_show(root: Path, ref: str, path: PurePosixPath) -> str | None:
    result = subprocess.run(
        ["git", "-C", str(root), "show", f"{ref}:{path.as_posix()}"],
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    return result.stdout.decode("utf-8")


def identity(entry: CatalogEntry) -> str:
    return f"{entry['module_name']}@{entry['version']}"


def retained_resource_root(module_name: str, version: str) -> str:
    return f"data/terminology/versions/{module_name}/{version}/{module_name}"


def bundle_digest(bundle_root: Path) -> str:
    """Digest every YAML file a retained release can serve."""

    return knowledge_base_content_sha256(bundle_root)


def _config_identity(module_dir: Path) -> tuple[str, str] | None:
    config_path = module_dir / "config.yaml"
    if not config_path.is_file():
        return None
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        return None
    return str(raw.get("name")), str(raw.get("version"))


# --------------------------------------------------------------------------- #
# status
# --------------------------------------------------------------------------- #


def collect_status(repo: Repository) -> list[ReleaseReport]:
    _payload, entries = repo.read_catalog()
    committed = repo.committed_catalog()
    committed_by_identity = (
        {identity(entry): entry for entry in committed} if committed else {}
    )
    pins = repo.read_pins()
    reports: list[ReleaseReport] = []

    for entry in entries:
        report = ReleaseReport(
            identity(entry), "default" if entry["default"] else "retained"
        )
        _check_release(repo, entry, committed_by_identity, pins, report)
        reports.append(report)

    current = {identity(entry) for entry in entries}
    for removed in sorted(committed_by_identity.keys() - current):
        report = ReleaseReport(removed, "removed")
        report.add(
            "FAIL",
            "This release is in the committed catalog but no longer in the working "
            "catalog. Hosts may have pinned it.",
            f"Restore its catalog entry and files (`git restore {CATALOG_PATH}`). "
            "Removing a release is only acceptable if it never shipped in an "
            "lx-dtypes package.",
        )
        reports.append(report)

    retained = {identity(entry) for entry in entries if not entry["default"]}
    for stale in sorted(pins.keys() - retained):
        report = ReleaseReport(stale, "pin")
        report.add(
            "FAIL",
            f"{PINS_PATH} pins this release but the catalog no longer lists it "
            "as retained.",
            "Retained releases must stay retained. Restore the catalog entry; do "
            "not delete the pin.",
        )
        reports.append(report)
    return reports


def _check_release(
    repo: Repository,
    entry: CatalogEntry,
    committed: dict[str, CatalogEntry],
    pins: dict[str, str],
    report: ReleaseReport,
) -> None:
    module_name = str(entry["module_name"])
    version = str(entry["version"])
    is_default = bool(entry["default"])
    module_dir = repo.module_dir(entry)
    module_path = repo.repo_path(module_dir)
    committed_entry = committed.get(report.identity)
    is_committed = committed_entry is not None

    if not module_dir.is_dir():
        report.add(
            "FAIL",
            f"Release directory {module_path} does not exist.",
            f"`git restore {module_path}` or correct `resource_root` in {CATALOG_PATH}.",
        )
        return

    config_identity = _config_identity(module_dir)
    if config_identity != (module_name, version):
        declared = "@".join(config_identity) if config_identity else "nothing"
        fix = f"`git restore {module_path}/config.yaml`."
        if is_default and config_identity and config_identity[0] == module_name:
            fix += (
                " To publish a new version, do not edit `version` by hand: run "
                f"`{TOOL} new-version {module_name} {config_identity[1]}` after "
                "restoring it."
            )
        report.add(
            "FAIL",
            f"config.yaml declares {declared}, but the catalog lists {report.identity}.",
            fix,
        )

    actual = knowledge_base_content_sha256(module_dir)
    expected = str(entry["content_sha256"])
    if actual != expected:
        message = (
            f"YAML files differ from the catalog digest "
            f"(catalog {expected[:12]}…, files {actual[:12]}…)."
        )
        if not is_default:
            report.add(
                "FAIL",
                message + " Retained releases are frozen.",
                f"`git restore {module_path}`; make corrections in the default "
                f"release and run `{TOOL} new-version {module_name} <next-version>`.",
            )
        elif is_committed:
            report.add(
                "FAIL",
                message + " This release is committed and may have shipped; "
                "editing it in place changes pinned terminology.",
                f"Keep the edit as a new version: `{TOOL} new-version {module_name} "
                f"<next-version>` (retains the committed bytes), or discard it with "
                f"`git restore {module_path}`.",
            )
        else:
            report.add(
                "WARN",
                message + " This version is not committed yet, so it is still a "
                "draft.",
                f"After reviewing the edits run `{TOOL} refresh-digest {module_name}`.",
            )

    if committed_entry is not None and committed_entry["content_sha256"] != expected:
        report.add(
            "FAIL",
            "The catalog digest of this committed release was changed. Hosts that "
            "pinned the old digest will refuse to load it.",
            f"Restore the entry's `content_sha256` from git and publish the change "
            f"with `{TOOL} new-version {module_name} <next-version>`. Only if "
            f"{report.identity} never shipped in an lx-dtypes package may its "
            f"digest be refreshed with `{TOOL} refresh-digest {module_name} "
            "--allow-committed`.",
        )

    if not is_default:
        _check_retained(repo, entry, pins, report)


def _check_retained(
    repo: Repository,
    entry: CatalogEntry,
    pins: dict[str, str],
    report: ReleaseReport,
) -> None:
    module_name = str(entry["module_name"])
    version = str(entry["version"])
    expected_root = retained_resource_root(module_name, version)
    if entry["resource_root"] != expected_root:
        report.add(
            "FAIL",
            f"Retained releases must live in {expected_root}, not "
            f"{entry['resource_root']}; otherwise they share files with another "
            "version.",
            f"Use `{TOOL} new-version` to retain releases; it creates this layout.",
        )
        return
    bundle_root = repo.module_dir(entry).parent
    bundle_path = repo.repo_path(bundle_root)
    pinned = pins.get(report.identity)
    if pinned is None:
        report.add(
            "FAIL",
            f"No bundle pin in {PINS_PATH}; its snapshotted dependencies are "
            "unprotected.",
            f"Add \"{report.identity}\": \"{bundle_digest(bundle_root)}\" after "
            "confirming the bundle matches the release that shipped.",
        )
    elif bundle_digest(bundle_root) != pinned:
        report.add(
            "FAIL",
            f"The retained bundle {bundle_path} (module or snapshotted "
            "dependencies) differs from its pin.",
            f"`git restore {bundle_path}`. Retained bundles are frozen; correct the "
            f"default release and run `{TOOL} new-version {module_name} <next-version>`.",
        )


def print_status(reports: Sequence[ReleaseReport], *, verbose: bool) -> int:
    failures = sum(
        1 for report in reports for problem in report.problems if problem.severity == "FAIL"
    )
    warnings_count = sum(
        1 for report in reports for problem in report.problems if problem.severity == "WARN"
    )
    for report in reports:
        if not report.problems:
            if verbose:
                print(f"OK    {report.identity:<45} {report.role}")
            continue
        worst = "FAIL" if any(p.severity == "FAIL" for p in report.problems) else "WARN"
        print(f"{worst:<5} {report.identity:<45} {report.role}")
        for problem in report.problems:
            print(f"      - {problem.message}")
            print(f"        fix: {problem.fix}")
    healthy = sum(1 for report in reports if not report.problems)
    print(
        f"\n{len(reports)} checked: {healthy} OK, {failures} failure(s), "
        f"{warnings_count} warning(s). Guide: {RELEASE_GUIDE}"
    )
    return 1 if failures else 0


# --------------------------------------------------------------------------- #
# new-version
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class NewVersionPlan:
    module_name: str
    old_version: str
    new_version: str
    retained_root: Path
    copied_dirs: tuple[str, ...]
    files_mentioning_old_version: tuple[str, ...]
    new_digest: str
    bundle_digest: str


def closure_directories(search_root: Path, module_name: str) -> tuple[Path, ...]:
    """Return the top-level directories a load of ``module_name`` reads."""

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        loader = DataLoader(input_dirs=[search_root])
        loader.load_module_configs()
        configs = loader.resolved_module_configs(module_name)
    directories: set[Path] = set()
    for config in configs:
        if config.source_file is None:
            raise CatalogToolError(f"Module {config.name} has no source file.")
        directories.add(config.source_file.parent.resolve())
    return tuple(
        sorted(
            directory
            for directory in directories
            if not any(
                other != directory and directory.is_relative_to(other)
                for other in directories
            )
        )
    )


def _default_entry(entries: list[CatalogEntry], module_name: str) -> CatalogEntry:
    for entry in entries:
        if entry["module_name"] == module_name and entry["default"]:
            return entry
    known = sorted({str(entry["module_name"]) for entry in entries})
    raise CatalogToolError(
        f"No default release of {module_name!r} in {CATALOG_PATH}. "
        f"Known modules: {', '.join(known)}."
    )


def _source_tree(repo: Repository, from_ref: str, scratch: Path) -> Path:
    """Return a repository root holding the package data as of ``from_ref``.

    The dependency closure is resolved inside this tree, so a retained bundle
    snapshots the dependencies as they were published, not as they are now.
    """

    if from_ref == "WORKTREE":
        return repo.root
    result = subprocess.run(
        [
            "git",
            "-C",
            str(repo.root),
            "archive",
            "--format=tar",
            from_ref,
            "--",
            "lx_dtypes/data",
        ],
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise CatalogToolError(
            f"Could not read package data from git ref {from_ref!r}: "
            f"{result.stderr.decode('utf-8', 'replace').strip()}\n"
            "If the release has never been committed, pass `--from-ref WORKTREE`."
        )
    tree = scratch / "source"
    tree.mkdir()
    with tarfile.open(fileobj=io.BytesIO(result.stdout)) as archive:
        archive.extractall(tree, filter="data")
    return tree


def _stage_bundle(sources: Sequence[Path], destination: Path) -> None:
    """Copy each closure directory to ``destination/<name>``."""

    names = [source.name for source in sources]
    duplicates = sorted({name for name in names if names.count(name) > 1})
    if duplicates:
        raise CatalogToolError(
            "Dependency directories share a name and cannot be flattened into one "
            f"retained bundle: {', '.join(duplicates)}. Retain this release by hand "
            f"following {RELEASE_GUIDE}."
        )
    destination.mkdir(parents=True)
    for source in sources:
        shutil.copytree(source, destination / source.name)


def _bump_config_version(config_path: Path, old: str, new: str) -> str:
    text = config_path.read_text(encoding="utf-8")
    pattern = VERSION_LINE_RE.format(old=re.escape(old))
    updated, count = re.subn(pattern, rf"\g<1>\g<2>{new}\g<2>\g<3>", text)
    if count != 1:
        raise CatalogToolError(
            f"Expected exactly one `version: {old}` line in {config_path}; found "
            f"{count}. Set the version by hand and rerun with care."
        )
    return updated


def _files_mentioning(root: Path, needle: str, exclude: Path) -> tuple[str, ...]:
    hits: list[str] = []
    for path in sorted(root.rglob("*")):
        if path == exclude or path.suffix.lower() not in {".yaml", ".yml"}:
            continue
        if re.search(rf"(?<![\w.]){re.escape(needle)}(?![\w.])", path.read_text("utf-8")):
            hits.append(path.relative_to(root).as_posix())
    return tuple(hits)


def new_version(
    repo: Repository,
    module_name: str,
    new: str,
    *,
    from_ref: str = "HEAD",
    dry_run: bool = False,
) -> NewVersionPlan:
    payload, entries = repo.read_catalog()
    entry = _default_entry(entries, module_name)
    old = str(entry["version"])
    if new == old or any(
        e["module_name"] == module_name and e["version"] == new for e in entries
    ):
        raise CatalogToolError(
            f"{module_name}@{new} already exists in {CATALOG_PATH}; choose a version "
            "that was never published."
        )
    pins = repo.read_pins()
    old_identity = f"{module_name}@{old}"
    if old_identity in pins:
        raise CatalogToolError(f"{old_identity} is already pinned as retained.")

    live_dir = repo.module_dir(entry)
    if live_dir.name != module_name:
        raise CatalogToolError(
            f"Live directory {repo.repo_path(live_dir)} is not named {module_name}; "
            f"retain this release by hand following {RELEASE_GUIDE}."
        )
    retained_root = repo.root / VERSIONS_PATH / module_name / old
    if retained_root.exists():
        raise CatalogToolError(
            f"{repo.repo_path(retained_root)} already exists. Remove a partial "
            "earlier attempt or inspect it before retrying."
        )

    with tempfile.TemporaryDirectory() as scratch:
        source_root = _source_tree(repo, from_ref, Path(scratch))
        source_dir = source_root / "lx_dtypes" / str(entry["resource_root"])
        if not (source_dir / "config.yaml").is_file():
            raise CatalogToolError(
                f"{old_identity} has no config.yaml at git ref {from_ref!r}. Commit "
                "the release first or pass `--from-ref WORKTREE`."
            )
        search_root = module_search_root(source_dir / "config.yaml")
        sources = closure_directories(search_root, module_name)
        staged = Path(scratch) / "bundle"
        _stage_bundle(sources, staged)
        snapshot_digest = knowledge_base_content_sha256(staged / module_name)
        if snapshot_digest != entry["content_sha256"]:
            raise CatalogToolError(
                f"The files of {old_identity} at {from_ref!r} do not match its catalog "
                "digest, so they are not the published release.\n"
                "The edit was probably already committed. Find the commit that "
                "published it (`git log --oneline -- "
                f"{repo.repo_path(live_dir)} {CATALOG_PATH}`) and rerun with "
                "`--from-ref <commit>`."
            )
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            loader = DataLoader(input_dirs=[staged])
            loader.load_module_configs()
            loaded = loader.load_knowledge_base(module_name)
        if loaded.config.version != old:
            raise CatalogToolError(
                f"The retained bundle loads {module_name}@{loaded.config.version}, "
                f"expected {old}."
            )
        retained_bundle_digest = bundle_digest(staged)

        config_path = live_dir / "config.yaml"
        bumped_config = _bump_config_version(config_path, old, new)
        mentions = _files_mentioning(live_dir, old, exclude=config_path)

        if dry_run:
            original = config_path.read_text(encoding="utf-8")
            config_path.write_text(bumped_config, encoding="utf-8")
            try:
                new_digest = knowledge_base_content_sha256(live_dir)
            finally:
                config_path.write_text(original, encoding="utf-8")
        else:
            retained_root.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(staged, retained_root)
            config_path.write_text(bumped_config, encoding="utf-8")
            new_digest = knowledge_base_content_sha256(live_dir)

    plan = NewVersionPlan(
        module_name=module_name,
        old_version=old,
        new_version=new,
        retained_root=retained_root,
        copied_dirs=tuple(source.name for source in sources),
        files_mentioning_old_version=mentions,
        new_digest=new_digest,
        bundle_digest=retained_bundle_digest,
    )
    if dry_run:
        return plan

    index = entries.index(entry)
    retained_entry: CatalogEntry = {
        **entry,
        "resource_root": retained_resource_root(module_name, old),
        "default": False,
    }
    new_entry: CatalogEntry = {**entry, "version": new, "content_sha256": new_digest}
    entries[index : index + 1] = [new_entry, retained_entry]
    repo.write_catalog(payload, entries)
    repo.write_pins({**pins, old_identity: retained_bundle_digest})
    return plan


def print_new_version(repo: Repository, plan: NewVersionPlan, *, dry_run: bool) -> None:
    verb = "Would retain" if dry_run else "Retained"
    print(
        f"{verb} {plan.module_name}@{plan.old_version} in "
        f"{repo.repo_path(plan.retained_root)} with: {', '.join(plan.copied_dirs)}"
    )
    print(
        f"{'Would set' if dry_run else 'Set'} {plan.module_name} config.yaml version "
        f"{plan.old_version} -> {plan.new_version} (new default)."
    )
    if dry_run:
        print("Dry run: nothing was written.")
        return
    print(f"Updated {CATALOG_PATH} and pinned the retained bundle in {PINS_PATH}.")
    if plan.files_mentioning_old_version:
        print(
            f"\nReview these files that still mention {plan.old_version} "
            "(for example rule sidecars with their own version):"
        )
        for path in plan.files_mentioning_old_version:
            print(f"  - {path}")
    print(
        "\nNext steps:\n"
        f"  1. Make or keep your terminology edits in the live {plan.module_name} directory.\n"
        f"  2. Run `{TOOL} refresh-digest {plan.module_name}` after every edit.\n"
        "  3. Describe the release in CHANGELOG.md under [Unreleased].\n"
        f"  4. Run `{TOOL} status` and the checks listed in {RELEASE_GUIDE}."
    )


# --------------------------------------------------------------------------- #
# refresh-digest
# --------------------------------------------------------------------------- #


def refresh_digest(
    repo: Repository,
    module_name: str,
    *,
    allow_committed: bool = False,
) -> tuple[str, str, str]:
    payload, entries = repo.read_catalog()
    entry = _default_entry(entries, module_name)
    release = identity(entry)
    live_dir = repo.module_dir(entry)
    if _config_identity(live_dir) != (module_name, entry["version"]):
        raise CatalogToolError(
            f"config.yaml of {release} declares a different identity. Restore it, "
            f"then use `{TOOL} new-version {module_name} <next-version>` to change "
            "the version."
        )
    old = str(entry["content_sha256"])
    new = knowledge_base_content_sha256(live_dir)
    if new == old:
        return release, old, new
    committed = repo.committed_catalog() or []
    committed_entry = next((e for e in committed if identity(e) == release), None)
    if committed_entry is not None and not allow_committed:
        raise CatalogToolError(
            f"{release} is in the committed catalog, so it may already have shipped "
            "and been pinned by hosts. Refusing to change its digest.\n"
            f"Publish the edit as a new version instead: `{TOOL} new-version "
            f"{module_name} <next-version>`.\n"
            f"Only if {release} never shipped in an lx-dtypes package, rerun with "
            "`--allow-committed`."
        )
    entry["content_sha256"] = new
    repo.write_catalog(payload, entries)
    return release, old, new


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--repo-root", type=Path, default=REPO_ROOT, help=argparse.SUPPRESS
    )
    commands = parser.add_subparsers(dest="command", required=True)

    status = commands.add_parser("status", help="Diagnose every catalog release.")
    status.add_argument(
        "-v", "--verbose", action="store_true", help="Also list healthy releases."
    )

    new = commands.add_parser(
        "new-version",
        help="Retain the current default release and start a new version.",
    )
    new.add_argument("module", help="Module name, for example coloreg.")
    new.add_argument("version", help="The new version, for example 0.4.0.")
    new.add_argument(
        "--from-ref",
        default="HEAD",
        help=(
            "Git ref holding the published bytes to retain (default HEAD). "
            "Use WORKTREE to retain the working tree as-is."
        ),
    )
    new.add_argument(
        "--dry-run", action="store_true", help="Verify and report without writing."
    )

    refresh = commands.add_parser(
        "refresh-digest",
        help="Update the catalog digest of an unreleased default release.",
    )
    refresh.add_argument("module", help="Module name.")
    refresh.add_argument(
        "--allow-committed",
        action="store_true",
        help="Allow refreshing a committed release that never shipped in a package.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repo = Repository(Path(args.repo_root).resolve())
    try:
        if args.command == "status":
            return print_status(collect_status(repo), verbose=args.verbose)
        if args.command == "new-version":
            plan = new_version(
                repo,
                args.module,
                args.version,
                from_ref=args.from_ref,
                dry_run=args.dry_run,
            )
            print_new_version(repo, plan, dry_run=args.dry_run)
            return 0
        release, old, new = refresh_digest(
            repo, args.module, allow_committed=args.allow_committed
        )
        if old == new:
            print(f"{release}: catalog digest is already current.")
        else:
            print(f"{release}: catalog digest {old[:12]}… -> {new[:12]}…")
        return 0
    except CatalogToolError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
