#!/usr/bin/env python3
"""Release helper for lx-dtypes.

``prepare X.Y.Z`` sets the package version in every tracked release file and
refreshes ``uv.lock``. ``check-version`` reports files that disagree with
``pyproject.toml``. Knowledge-base module versions are independent of the
package version and are never changed.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import re
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path, PurePosixPath

VERSION_RE = re.compile(r"^\d+\.\d+\.\d+(?:[A-Za-z0-9._+-]*)?$")
PROJECT_VERSION_RE = re.compile(r'(?ms)^(\[project\].*?^\s*version\s*=\s*")([^"]+)(")')
INIT_VERSION_RE = re.compile(r'(?m)^(__version__\s*=\s*")([^"]+)(")')
CITATION_VERSION_RE = re.compile(
    r"""(?m)^(version:[ \t]*)["']?([^"'\s]+)["']?[ \t]*$"""
)
CITATION_DATE_RE = re.compile(r"(?m)^(date-released:[ \t]*)\S+[ \t]*$")
LOCK_VERSION_RE = re.compile(
    r'(?m)^\[\[package\]\]\nname = "lx-dtypes"\nversion = "([^"]+)"$'
)
CHANGELOG_UNRELEASED_RE = re.compile(r"(?m)^## \[Unreleased\][ \t]*$")
MIGRATION_FILE_RE = re.compile(r"^\d{4}_.+\.py$")
MIGRATION_PACKAGE_PATH = PurePosixPath("lx_dtypes/django/migrations")
KNOWLEDGE_BASE_DATA_PATH = PurePosixPath("lx_dtypes/data")


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _pyproject_path() -> Path:
    return _project_root() / "pyproject.toml"


def _init_path() -> Path:
    return _project_root() / "lx_dtypes" / "__init__.py"


def _citation_path() -> Path:
    return _project_root() / "CITATION.cff"


def _changelog_path() -> Path:
    return _project_root() / "CHANGELOG.md"


def _lock_path() -> Path:
    return _project_root() / "uv.lock"


def _validate_version(version: str) -> str:
    if not VERSION_RE.fullmatch(version):
        raise SystemExit(
            f"Invalid version '{version}'. Expected a PEP 440 style version like 0.1.2."
        )
    return version


def read_project_version() -> str:
    pyproject_text = _pyproject_path().read_text()
    match = PROJECT_VERSION_RE.search(pyproject_text)
    if match is None:
        raise SystemExit("Could not find [project].version in pyproject.toml.")
    return match.group(2)


def write_project_version(version: str) -> None:
    pyproject_path = _pyproject_path()
    pyproject_text = pyproject_path.read_text()
    updated_pyproject, count = PROJECT_VERSION_RE.subn(
        rf"\g<1>{version}\g<3>",
        pyproject_text,
        count=1,
    )
    if count != 1:
        raise SystemExit("Could not update [project].version in pyproject.toml.")
    pyproject_path.write_text(updated_pyproject)

    init_path = _init_path()
    if init_path.exists():
        init_text = init_path.read_text()
        updated_init, init_count = INIT_VERSION_RE.subn(
            rf"\g<1>{version}\g<3>",
            init_text,
            count=1,
        )
        if init_count == 1:
            init_path.write_text(updated_init)


def write_citation_version(version: str, release_date: datetime.date) -> None:
    """Set ``version`` and ``date-released`` in CITATION.cff."""
    path = _citation_path()
    text = path.read_text(encoding="utf-8")
    # Quote the version: YAML would read an unquoted "1.0" as a number.
    text, count = CITATION_VERSION_RE.subn(rf'\g<1>"{version}"', text, count=1)
    if count != 1:
        raise SystemExit("Could not find version in CITATION.cff.")
    date_line = f"date-released: {release_date.isoformat()}"
    text, count = CITATION_DATE_RE.subn(date_line, text, count=1)
    if count != 1:
        text = text.rstrip("\n") + f"\n{date_line}\n"
    path.write_text(text, encoding="utf-8")


def update_changelog_heading(version: str) -> str:
    """Name the ``[Unreleased]`` section after ``version`` and describe the result.

    Release notes are never written or invented here. If the changelog has
    neither a section for ``version`` nor an ``[Unreleased]`` section, the
    maintainer must add one.
    """
    path = _changelog_path()
    text = path.read_text(encoding="utf-8")
    if re.search(rf"(?m)^## \[{re.escape(version)}\]", text):
        return f"CHANGELOG.md already has a section for {version}."
    text, count = CHANGELOG_UNRELEASED_RE.subn(
        f"## [{version}] - Unreleased", text, count=1
    )
    if count == 1:
        path.write_text(text, encoding="utf-8")
        return f"Renamed the [Unreleased] section of CHANGELOG.md to [{version}]."
    return f"Add a '## [{version}]' section with release notes to CHANGELOG.md."


def read_version_locations() -> dict[str, str | None]:
    """Return the version recorded in each release file (``None`` if absent)."""
    locations: dict[str, str | None] = {"pyproject.toml": read_project_version()}
    init_path = _init_path()
    if init_path.exists():
        match = INIT_VERSION_RE.search(init_path.read_text(encoding="utf-8"))
        if match is not None:
            locations["lx_dtypes/__init__.py"] = match.group(2)
    citation_path = _citation_path()
    if citation_path.exists():
        match = CITATION_VERSION_RE.search(citation_path.read_text(encoding="utf-8"))
        locations["CITATION.cff"] = match.group(2) if match else None
    lock_path = _lock_path()
    if lock_path.exists():
        match = LOCK_VERSION_RE.search(lock_path.read_text(encoding="utf-8"))
        locations["uv.lock"] = match.group(1) if match else None
    return locations


def version_mismatches() -> list[str]:
    """Describe every release file that disagrees with ``pyproject.toml``."""
    locations = read_version_locations()
    expected = locations["pyproject.toml"]
    problems = [
        f"{name}: {found or 'missing'} (expected {expected})"
        for name, found in locations.items()
        if found != expected
    ]
    changelog_path = _changelog_path()
    if changelog_path.exists() and expected is not None:
        changelog = changelog_path.read_text(encoding="utf-8")
        if not re.search(rf"(?m)^## \[{re.escape(expected)}\]", changelog):
            problems.append(f"CHANGELOG.md: no section for {expected}")
    return problems


def run_command(args: list[str], *, cwd: Path) -> None:
    completed = subprocess.run(args, cwd=cwd, check=False)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def _migration_contract_from_entries(
    entries: dict[PurePosixPath, bytes],
    *,
    root: PurePosixPath,
    label: str,
) -> tuple[tuple[tuple[str, str], ...], str]:
    migration_files = tuple(
        sorted(
            (path.name, hashlib.sha256(contents).hexdigest())
            for path, contents in entries.items()
            if path.parent == root and MIGRATION_FILE_RE.fullmatch(path.name)
        )
    )
    migration_names = frozenset(filename for filename, _digest in migration_files)
    max_migration_path = root / "max_migration.txt"
    try:
        max_migration = entries[max_migration_path].decode("utf-8").strip()
    except KeyError as exc:
        raise SystemExit(f"{label} does not contain {max_migration_path}.") from exc
    except UnicodeDecodeError as exc:
        raise SystemExit(f"{label} contains a non-UTF-8 max_migration.txt.") from exc
    if f"{max_migration}.py" not in migration_names:
        raise SystemExit(
            f"{label} names missing migration {max_migration!r} as its canonical maximum."
        )
    return migration_files, max_migration


def _source_migration_contract(root: Path) -> tuple[tuple[tuple[str, str], ...], str]:
    migration_root = root / MIGRATION_PACKAGE_PATH
    entries = {
        MIGRATION_PACKAGE_PATH / path.name: path.read_bytes()
        for path in migration_root.iterdir()
        if path.is_file()
    }
    return _migration_contract_from_entries(
        entries,
        root=MIGRATION_PACKAGE_PATH,
        label="source migration package",
    )


def _artifact_migration_contract(
    artifact: Path,
    *,
    version: str,
) -> tuple[tuple[tuple[str, str], ...], str]:
    if artifact.suffix == ".whl":
        with zipfile.ZipFile(artifact) as archive:
            entries = {
                PurePosixPath(name): archive.read(name)
                for name in archive.namelist()
                if not name.endswith("/")
            }
        contract_root = MIGRATION_PACKAGE_PATH
    elif artifact.name.endswith(".tar.gz"):
        with tarfile.open(artifact, mode="r:gz") as archive:
            entries = {
                PurePosixPath(member.name): extracted.read()
                for member in archive.getmembers()
                if member.isfile()
                and (extracted := archive.extractfile(member)) is not None
            }
        contract_root = PurePosixPath(f"lx_dtypes-{version}") / MIGRATION_PACKAGE_PATH
    else:
        raise SystemExit(f"Unsupported release artifact: {artifact.name}")
    return _migration_contract_from_entries(
        entries,
        root=contract_root,
        label=artifact.name,
    )


def verify_migration_artifacts(
    root: Path,
    *,
    version: str,
    artifacts: list[Path],
) -> None:
    source_contract = _source_migration_contract(root)
    for artifact in artifacts:
        artifact_contract = _artifact_migration_contract(artifact, version=version)
        if artifact_contract != source_contract:
            raise SystemExit(
                f"{artifact.name} migration contract differs from the source tree: "
                f"expected {source_contract}, found {artifact_contract}."
            )


def _source_knowledge_base_contract(root: Path) -> tuple[tuple[str, str], ...]:
    data_root = root / KNOWLEDGE_BASE_DATA_PATH
    return tuple(
        sorted(
            (
                path.relative_to(root).as_posix(),
                hashlib.sha256(path.read_bytes()).hexdigest(),
            )
            for path in data_root.rglob("*")
            if path.is_file() and path.name != ".gitkeep"
        )
    )


def _artifact_knowledge_base_contract(
    artifact: Path,
    *,
    version: str,
) -> tuple[tuple[str, str], ...]:
    if artifact.suffix == ".whl":
        with zipfile.ZipFile(artifact) as archive:
            entries = {
                PurePosixPath(name): archive.read(name)
                for name in archive.namelist()
                if not name.endswith("/")
            }
        artifact_root = PurePosixPath()
    elif artifact.name.endswith(".tar.gz"):
        with tarfile.open(artifact, mode="r:gz") as archive:
            entries = {
                PurePosixPath(member.name): extracted.read()
                for member in archive.getmembers()
                if member.isfile()
                and (extracted := archive.extractfile(member)) is not None
            }
        artifact_root = PurePosixPath(f"lx_dtypes-{version}")
    else:
        raise SystemExit(f"Unsupported release artifact: {artifact.name}")

    data_root = artifact_root / KNOWLEDGE_BASE_DATA_PATH
    return tuple(
        sorted(
            (
                (KNOWLEDGE_BASE_DATA_PATH / path.relative_to(data_root)).as_posix(),
                hashlib.sha256(contents).hexdigest(),
            )
            for path, contents in entries.items()
            if path.is_relative_to(data_root) and path.name != ".gitkeep"
        )
    )


def verify_knowledge_base_artifacts(
    root: Path,
    *,
    version: str,
    artifacts: list[Path],
) -> None:
    """Require release artifacts to contain the exact source terminology data."""
    source_contract = _source_knowledge_base_contract(root)
    if not source_contract:
        raise SystemExit("Source knowledge-base data contract is empty.")
    for artifact in artifacts:
        artifact_contract = _artifact_knowledge_base_contract(
            artifact,
            version=version,
        )
        if artifact_contract != source_contract:
            raise SystemExit(
                f"{artifact.name} knowledge-base data contract differs from the "
                "source tree."
            )


def cmd_current(_: argparse.Namespace) -> int:
    print(read_project_version())
    return 0


def verify_storage_artifacts(*, version: str, artifacts: list[Path]) -> None:
    """Require library-only archive roots, including for symlink entries."""
    sdist_roots = {
        ".gitignore",  # Hatch includes VCS exclusion rules when rebuilding wheels.
        "lx_dtypes",
        "lx_kb_lint.py",
        "pyproject.toml",
        "README.md",
        "LICENSE",
        "CHANGELOG.md",
        "CITATION.cff",
        "PKG-INFO",
    }
    for artifact in artifacts:
        if artifact.suffix == ".whl":
            with zipfile.ZipFile(artifact) as archive:
                names = archive.namelist()
            root = PurePosixPath()
        elif artifact.name.endswith(".tar.gz"):
            with tarfile.open(artifact, mode="r:gz") as archive:
                names = archive.getnames()
            root = PurePosixPath(f"lx_dtypes-{version}")
        else:
            raise SystemExit(f"Unsupported release artifact: {artifact.name}")
        for name in names:
            path = PurePosixPath(name)
            if not path.is_relative_to(root) or ".." in path.parts:
                raise SystemExit(f"{artifact.name} contains invalid member: {name}")
            relative = path.relative_to(root)
            if not relative.parts:
                continue
            top = relative.parts[0]
            allowed = (
                top in sdist_roots
                if artifact.name.endswith(".tar.gz")
                else top
                in {"lx_dtypes", "lx_kb_lint.py", f"lx_dtypes-{version}.dist-info"}
            )
            if not allowed:
                raise SystemExit(
                    f"{artifact.name} contains generated/runtime storage or "
                    f"repository-only files: {name}"
                )


def cmd_prepare(args: argparse.Namespace) -> int:
    version = _validate_version(args.version)
    current = read_project_version()
    write_project_version(version)
    print(f"pyproject.toml: {current} -> {version}")
    if _citation_path().exists():
        write_citation_version(version, args.release_date)
        print(f"CITATION.cff: {version}, released {args.release_date.isoformat()}")
    if _changelog_path().exists():
        print(update_changelog_heading(version))
    if args.lock:
        run_command(["uv", "lock"], cwd=_project_root())
        print("uv.lock: refreshed")
    else:
        print("uv.lock: not refreshed (--no-lock); run 'uv lock' before committing")

    problems = version_mismatches()
    for problem in problems:
        print(f"Still inconsistent: {problem}")
    print("Next steps:")
    print(f"  1. Review the release notes for {version} in CHANGELOG.md")
    print("  2. Run: lx-dtypes-release build")
    print(f"  3. Tag and push: git tag v{version} && git push origin v{version}")
    print("  4. Publish via GitHub release or workflow_dispatch")
    return 0


def cmd_check_version(_: argparse.Namespace) -> int:
    problems = version_mismatches()
    if not problems:
        print(f"All release files use version {read_project_version()}.")
        return 0
    for problem in problems:
        print(problem, file=sys.stderr)
    return 1


def _release_date(value: str) -> datetime.date:
    try:
        return datetime.date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"Expected YYYY-MM-DD, got {value!r}."
        ) from exc


def cmd_build(_: argparse.Namespace) -> int:
    root = _project_root()
    version = read_project_version()
    run_command([sys.executable, "-m", "build"], cwd=root)
    dist_paths = sorted((root / "dist").glob(f"lx_dtypes-{version}*"))
    if len(dist_paths) != 2:
        raise SystemExit(
            f"Expected exactly one wheel and one sdist for {version}; "
            f"found {len(dist_paths)} artifact(s)."
        )
    verify_storage_artifacts(version=version, artifacts=dist_paths)
    verify_migration_artifacts(root, version=version, artifacts=dist_paths)
    verify_knowledge_base_artifacts(root, version=version, artifacts=dist_paths)
    run_command(
        [
            sys.executable,
            "-m",
            "lx_dtypes.scripts.verify_packaged_report_templates",
        ],
        cwd=root,
    )
    run_command(
        [sys.executable, "-m", "twine", "check", *[str(path) for path in dist_paths]],
        cwd=root,
    )
    print(f"Built and validated lx-dtypes {version} artifacts only.")
    print(
        "Publish these artifacts through the protected GitHub workflow; "
        "do not upload dist/* from a reused local directory."
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Prepare and validate lx-dtypes package releases."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    current_parser = subparsers.add_parser(
        "current", help="Print the current package version."
    )
    current_parser.set_defaults(func=cmd_current)

    prepare_parser = subparsers.add_parser(
        "prepare",
        help=(
            "Set the package version in pyproject.toml, CITATION.cff, CHANGELOG.md "
            "and uv.lock."
        ),
    )
    prepare_parser.add_argument("version", help="New package version, e.g. 0.1.2")
    prepare_parser.add_argument(
        "--release-date",
        type=_release_date,
        default=datetime.datetime.now(tz=datetime.UTC).astimezone().date(),
        help="date-released for CITATION.cff (YYYY-MM-DD, default: today)",
    )
    prepare_parser.add_argument(
        "--no-lock",
        dest="lock",
        action="store_false",
        help="do not run 'uv lock' afterwards",
    )
    prepare_parser.set_defaults(func=cmd_prepare)

    check_parser = subparsers.add_parser(
        "check-version",
        help="Fail if a release file disagrees with the pyproject.toml version.",
    )
    check_parser.set_defaults(func=cmd_check_version)

    build_parser = subparsers.add_parser(
        "build", help="Build sdist/wheel and run twine metadata checks."
    )
    build_parser.set_defaults(func=cmd_build)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
