#!/usr/bin/env python3
"""Small release helper for lx-dtypes."""

from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
import sys
import tarfile
import zipfile
from pathlib import Path
from pathlib import PurePosixPath

VERSION_RE = re.compile(r"^\d+\.\d+\.\d+(?:[A-Za-z0-9._+-]*)?$")
PROJECT_VERSION_RE = re.compile(r'(?ms)^(\[project\].*?^\s*version\s*=\s*")([^"]+)(")')
INIT_VERSION_RE = re.compile(r'(?m)^(__version__\s*=\s*")([^"]+)(")')
MIGRATION_FILE_RE = re.compile(r"^\d{4}_.+\.py$")
MIGRATION_PACKAGE_PATH = PurePosixPath("lx_dtypes/django/migrations")


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _pyproject_path() -> Path:
    return _project_root() / "pyproject.toml"


def _init_path() -> Path:
    return _project_root() / "lx_dtypes" / "__init__.py"


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


def cmd_current(_: argparse.Namespace) -> int:
    print(read_project_version())
    return 0


def cmd_prepare(args: argparse.Namespace) -> int:
    version = _validate_version(args.version)
    current = read_project_version()
    write_project_version(version)
    print(f"Updated version: {current} -> {version}")
    print("Next steps:")
    print(f"  1. Update CHANGELOG.md for {version}")
    print("  2. Refresh the lock: uv lock")
    print("  3. Run: lx-dtypes-release build")
    print(f"  4. Tag and push: git tag v{version} && git push origin v{version}")
    print("  5. Publish via GitHub release or workflow_dispatch")
    return 0


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
    verify_migration_artifacts(root, version=version, artifacts=dist_paths)
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
        "prepare", help="Update the package version in tracked release files."
    )
    prepare_parser.add_argument("version", help="New package version, e.g. 0.1.2")
    prepare_parser.set_defaults(func=cmd_prepare)

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
