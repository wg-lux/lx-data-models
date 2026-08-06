#!/usr/bin/env python3
"""Small release helper for lx-dtypes."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

VERSION_RE = re.compile(r"^\d+\.\d+\.\d+(?:[A-Za-z0-9._+-]*)?$")
PROJECT_VERSION_RE = re.compile(r'(?ms)^(\[project\].*?^\s*version\s*=\s*")([^"]+)(")')
INIT_VERSION_RE = re.compile(r'(?m)^(__version__\s*=\s*")([^"]+)(")')
YAML_VERSION_RE = re.compile(r"(?m)^(version:\s*)(\S+)(\s*)$")
NIX_ATTR_VERSION_RE = re.compile(r'(?m)^(\s*version\s*=\s*")([^"]+)(";\s*)$')
NIX_KB_MODULE_VERSION_RE = re.compile(
    r'(?m)^(\s*kbModuleVersion\s*=\s*")([^"]+)(";\s*)$'
)


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _pyproject_path() -> Path:
    return _project_root() / "pyproject.toml"


def _init_path() -> Path:
    return _project_root() / "lx_dtypes" / "__init__.py"


def _kb_config_paths() -> tuple[Path, ...]:
    root = _project_root()
    return (root / "lx_dtypes" / "data" / "star_upper_gi" / "config.yaml",)


def _kb_package_path() -> Path:
    return _project_root() / "package.nix"


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

    for kb_config_path in _kb_config_paths():
        if not kb_config_path.exists():
            continue
        kb_config_text = kb_config_path.read_text()
        updated_kb_config, kb_count = YAML_VERSION_RE.subn(
            rf"\g<1>{version}\g<3>",
            kb_config_text,
            count=1,
        )
        if kb_count == 1:
            kb_config_path.write_text(updated_kb_config)

    kb_package_path = _kb_package_path()
    if kb_package_path.exists():
        kb_package_text = kb_package_path.read_text()
        updated_kb_package, package_count = NIX_ATTR_VERSION_RE.subn(
            rf"\g<1>{version}\g<3>",
            kb_package_text,
            count=1,
        )
        if package_count == 1:
            updated_kb_package, _ = NIX_KB_MODULE_VERSION_RE.subn(
                rf"\g<1>{version}\g<3>",
                updated_kb_package,
                count=1,
            )
            kb_package_path.write_text(updated_kb_package)


def run_command(args: list[str], *, cwd: Path) -> None:
    completed = subprocess.run(args, cwd=cwd, check=False)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


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
    print("  2. Run: lx-dtypes-release build")
    print(f"  3. Tag and push: git tag v{version} && git push origin v{version}")
    print("  4. Publish via GitHub release or workflow_dispatch")
    return 0


def cmd_build(_: argparse.Namespace) -> int:
    root = _project_root()
    run_command([sys.executable, "-m", "build"], cwd=root)
    dist_paths = sorted((root / "dist").glob("*"))
    if not dist_paths:
        raise SystemExit("No build artifacts found under dist/.")
    run_command(
        [sys.executable, "-m", "twine", "check", *[str(path) for path in dist_paths]],
        cwd=root,
    )
    print("Built and validated dist artifacts.")
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
