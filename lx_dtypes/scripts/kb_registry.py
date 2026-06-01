#!/usr/bin/env python3
"""Manage a versioned knowledge-base registry for lx-dtypes."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

from lx_dtypes.models.interface.data_roots import resolve_default_data_root


def get_current_knowledge_base_identity(module_name: str) -> tuple[str, str]:
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
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


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
        "input_dirs": [str(path.expanduser().resolve()) for path in input_dirs]
    }
    if medical_field:
        entry["medical_field"] = medical_field
    module_versions[version] = entry
    _write_registry(registry_path, payload)


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
    module_name, version = get_current_knowledge_base_identity(args.module)
    medical_field = get_current_knowledge_base_medical_field(args.module)
    data_root = resolve_default_data_root()
    if data_root is None:
        raise SystemExit("Could not resolve a default lx-dtypes data root.")

    _add_entry(
        registry_path=registry_path,
        module_name=module_name,
        version=version,
        input_dirs=[data_root],
        medical_field=medical_field,
    )
    print(
        f"Registered current KB {module_name}@{version} in {registry_path} "
        f"from {data_root}."
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

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
