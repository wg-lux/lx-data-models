#!/usr/bin/env python3
"""Manage a versioned knowledge-base registry for lx-dtypes."""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any
import uuid

import yaml

from lx_dtypes.knowledge_bases import (
    BUILTIN_KNOWLEDGE_BASE_PROVIDER,
    get_packaged_knowledge_base,
)
from lx_dtypes.knowledge_base_registry import (
    DEFAULT_PACKAGED_KNOWLEDGE_BASE,
    bootstrap_packaged_knowledge_bases,
    configured_registry_path,
)
from lx_dtypes.models.interface.data_roots import resolve_default_data_root


def get_current_knowledge_base_identity(module_name: str) -> tuple[str, str]:
    try:
        descriptor = get_packaged_knowledge_base(module_name)
    except LookupError:
        pass
    else:
        return descriptor.module_name, descriptor.version

    data_root = resolve_default_data_root()
    if data_root is None:
        raise SystemExit("Could not resolve a default lx-dtypes data root.")

    config_path = data_root / module_name / "config.yaml"
    if not config_path.exists():
        raise SystemExit(
            f"Could not find config.yaml for module '{module_name}' at {config_path}."
        )

    payload = yaml.safe_load(config_path.read_text())
    if not isinstance(payload, dict):
        raise SystemExit(f"Malformed module config at {config_path}.")

    resolved_module_name = str(payload.get("name") or module_name).strip()
    version = str(payload.get("version") or "").strip()
    if not version:
        raise SystemExit(f"Module config at {config_path} does not define a version.")
    return resolved_module_name, version


def get_current_knowledge_base_medical_field(module_name: str) -> str | None:
    try:
        return get_packaged_knowledge_base(module_name).medical_field
    except LookupError:
        pass

    data_root = resolve_default_data_root()
    if data_root is None:
        raise SystemExit("Could not resolve a default lx-dtypes data root.")

    config_path = data_root / module_name / "config.yaml"
    if not config_path.exists():
        raise SystemExit(
            f"Could not find config.yaml for module '{module_name}' at {config_path}."
        )

    payload = yaml.safe_load(config_path.read_text())
    if not isinstance(payload, dict):
        raise SystemExit(f"Malformed module config at {config_path}.")
    value = payload.get("medical_field")
    return value.strip() if isinstance(value, str) and value.strip() else None


def _registry_payload(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"modules": {}}
    payload = json.loads(path.read_text())
    if not isinstance(payload, dict):
        raise SystemExit("Registry payload must be a JSON object.")
    modules = payload.get("modules")
    if modules is None:
        payload["modules"] = {}
    elif not isinstance(modules, dict):
        raise SystemExit("Registry 'modules' entry must be a JSON object.")
    return payload


def _write_registry(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    temporary_path = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temporary_path.open("w", encoding="utf-8") as registry_file:
            registry_file.write(serialized)
            registry_file.flush()
            os.fsync(registry_file.fileno())
        os.replace(temporary_path, path)
    finally:
        temporary_path.unlink(missing_ok=True)


def _add_entry(
    *,
    registry_path: Path,
    module_name: str,
    version: str,
    input_dirs: list[Path],
    medical_field: str | None = None,
) -> None:
    payload = _registry_payload(registry_path)
    modules = payload.setdefault("modules", {})
    module_versions = modules.setdefault(module_name, {})
    entry: dict[str, Any] = {
        "sources": [
            {
                "kind": "filesystem",
                "input_dirs": [str(path.expanduser().resolve()) for path in input_dirs],
            }
        ]
    }
    if medical_field:
        entry["medical_field"] = medical_field
    module_versions[version] = entry
    _write_registry(registry_path, payload)


def _add_packaged_entry(*, registry_path: Path, module_name: str) -> tuple[str, str]:
    descriptor = get_packaged_knowledge_base(module_name)
    payload = _registry_payload(registry_path)
    modules = payload.setdefault("modules", {})
    module_versions = modules.setdefault(descriptor.module_name, {})
    entry: dict[str, Any] = {
        "sources": [
            {
                "kind": "provider",
                "provider": BUILTIN_KNOWLEDGE_BASE_PROVIDER,
                "content_sha256": descriptor.content_sha256,
            }
        ]
    }
    if descriptor.medical_field:
        entry["medical_field"] = descriptor.medical_field
    existing_entry = module_versions.get(descriptor.version)
    if existing_entry is not None and existing_entry != entry:
        raise SystemExit(
            "Refusing to replace existing knowledge-base registry entry for "
            f"{descriptor.module_name}@{descriptor.version}."
        )
    if existing_entry == entry:
        return descriptor.module_name, descriptor.version
    module_versions[descriptor.version] = entry
    _write_registry(registry_path, payload)
    return descriptor.module_name, descriptor.version


def cmd_show(args: argparse.Namespace) -> int:
    registry_path = args.registry.expanduser().resolve()
    payload = _registry_payload(registry_path)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def cmd_add(args: argparse.Namespace) -> int:
    registry_path = args.registry.expanduser().resolve()
    input_dirs = [path.expanduser().resolve() for path in args.input_dir]
    _add_entry(
        registry_path=registry_path,
        module_name=args.module,
        version=args.version,
        input_dirs=input_dirs,
        medical_field=getattr(args, "medical_field", None),
    )
    print(
        f"Registered {args.module}@{args.version} in {registry_path} "
        f"with {len(input_dirs)} input dir(s)."
    )
    return 0


def cmd_add_current(args: argparse.Namespace) -> int:
    registry_path = args.registry.expanduser().resolve()
    try:
        module_name, version = _add_packaged_entry(
            registry_path=registry_path,
            module_name=args.module,
        )
    except LookupError as exc:
        raise SystemExit(str(exc)) from exc
    print(
        f"Registered current KB {module_name}@{version} in {registry_path} "
        f"from {BUILTIN_KNOWLEDGE_BASE_PROVIDER}."
    )
    return 0


def cmd_bootstrap(args: argparse.Namespace) -> int:
    """Strictly provision and validate the installed packaged catalog."""

    try:
        result = bootstrap_packaged_knowledge_bases(
            configured_registry_path(args.registry),
            default_module=args.module,
        )
    except Exception as exc:
        print(
            json.dumps(
                {
                    "event": "lx_dtypes.knowledge_base_bootstrap",
                    "status": "error",
                    "detail": str(exc),
                },
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 1

    print(
        json.dumps(
            {
                "event": "lx_dtypes.knowledge_base_bootstrap",
                "status": "ok",
                "registry": str(result.registry),
                "module": result.module_name,
                "version": result.version,
            },
            sort_keys=True,
        )
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create and update LX_DTYPES_KB_REGISTRY JSON files."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    show_parser = subparsers.add_parser("show", help="Print the registry JSON.")
    show_parser.add_argument("registry", type=Path, help="Registry JSON path.")
    show_parser.set_defaults(func=cmd_show)

    add_parser = subparsers.add_parser(
        "add", help="Add an explicit module/version entry."
    )
    add_parser.add_argument("registry", type=Path, help="Registry JSON path.")
    add_parser.add_argument(
        "--module", required=True, help="Knowledge-base module name."
    )
    add_parser.add_argument("--version", required=True, help="Knowledge-base version.")
    add_parser.add_argument(
        "--medical-field",
        default=None,
        help="Optional medical field metadata, for example gastroenterology.",
    )
    add_parser.add_argument(
        "--input-dir",
        action="append",
        required=True,
        type=Path,
        help="One input directory to provision for this module/version. Repeatable.",
    )
    add_parser.set_defaults(func=cmd_add)

    add_current_parser = subparsers.add_parser(
        "add-current",
        help="Register the currently installed module/version and resolved data root.",
    )
    add_current_parser.add_argument("registry", type=Path, help="Registry JSON path.")
    add_current_parser.add_argument(
        "--module",
        default="report_template_examples",
        help="Knowledge-base module name to resolve. Defaults to report_template_examples.",
    )
    add_current_parser.set_defaults(func=cmd_add_current)

    bootstrap_parser = subparsers.add_parser(
        "bootstrap",
        help="Strictly provision and validate all packaged knowledge bases.",
    )
    bootstrap_parser.add_argument(
        "--registry",
        type=Path,
        default=None,
        help="Registry path; defaults to LX_DTYPES_KB_REGISTRY.",
    )
    bootstrap_parser.add_argument(
        "--module",
        default=DEFAULT_PACKAGED_KNOWLEDGE_BASE,
        help=(
            "Packaged module to activate when no active identity exists. "
            f"Defaults to {DEFAULT_PACKAGED_KNOWLEDGE_BASE}."
        ),
    )
    bootstrap_parser.set_defaults(func=cmd_bootstrap)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
