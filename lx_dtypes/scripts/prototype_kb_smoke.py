#!/usr/bin/env python3
"""Resolve and load a versioned knowledge-base module through the registry."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

import django

from lx_dtypes.models.interface.KnowledgeBaseResolver import (
    KnowledgeBaseVersionNotFoundError,
    get_knowledge_base_identity,
    load_knowledge_base,
    resolve_versioned_input_dirs,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Smoke-test versioned knowledge-base resolution through "
            "LX_DTYPES_KB_REGISTRY."
        )
    )
    parser.add_argument("--module", required=True, help="Knowledge-base module name.")
    parser.add_argument(
        "--version", required=True, help="Explicit knowledge-base version."
    )
    parser.add_argument(
        "--django-settings-module",
        default="",
        help=(
            "Optional Django settings module to export before loading the KB. "
            "Defaults to lx_dtypes.django_settings_ci_test when unset and "
            "DJANGO_SETTINGS_MODULE is not already defined."
        ),
    )
    return parser


def build_payload(
    *,
    module_name: str,
    version: str,
    input_dirs: tuple[Path, ...],
    identity: tuple[str, str],
    kb: Any,
) -> dict[str, Any]:
    record_lists = kb.export_record_lists()
    return {
        "registry_path": os.getenv("LX_DTYPES_KB_REGISTRY", ""),
        "requested": {"module": module_name, "version": version},
        "resolved_identity": {"module": identity[0], "version": identity[1]},
        "input_dirs": [str(path) for path in input_dirs],
        "counts": {
            key: len(value)
            for key, value in record_lists.items()
            if isinstance(value, list)
        },
    }


def main() -> int:
    args = build_parser().parse_args()
    if args.django_settings_module:
        os.environ["DJANGO_SETTINGS_MODULE"] = args.django_settings_module
    else:
        os.environ["DJANGO_SETTINGS_MODULE"] = "lx_dtypes.django_settings_ci_test"
    django.setup()
    try:
        input_dirs = resolve_versioned_input_dirs(args.module, args.version)
        identity = get_knowledge_base_identity(args.module, version=args.version)
        kb = load_knowledge_base(args.module, version=args.version)
    except KnowledgeBaseVersionNotFoundError as exc:
        raise SystemExit(str(exc)) from exc

    print(
        json.dumps(
            build_payload(
                module_name=args.module,
                version=args.version,
                input_dirs=input_dirs,
                identity=identity,
                kb=kb,
            ),
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
