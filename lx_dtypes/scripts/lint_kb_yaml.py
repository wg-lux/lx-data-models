#!/usr/bin/env python3
"""Lint KB concept YAML files with explicit source locations."""

from __future__ import annotations

import argparse
from pathlib import Path

from lx_dtypes.utils.kb_yaml_lint import (
    discover_yaml_files,
    lint_kb_yaml_files,
    summarize_issues,
)


def parse_args() -> argparse.Namespace:
    project_root = Path(__file__).resolve().parents[2]
    default_data_path = project_root / "lx_dtypes" / "data"
    default_config_paths = [
        default_data_path / "sample_knowledge_base" / "config.yaml",
        default_data_path / "report_template_examples" / "config.yaml",
        default_data_path / "star_upper_gi" / "config.yaml",
    ]

    parser = argparse.ArgumentParser(
        description=(
            "Lint knowledge-base YAML concept files and report explicit "
            "file:line:column diagnostics."
        )
    )
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        default=[],
        help=(
            "YAML files or directories to lint. If omitted, canonical module "
            "configs are linted. If a path is 'config.yaml', its configured "
            "data files/dirs (including dependencies/modules) are linted."
        ),
    )
    parser.add_argument(
        "--config",
        action="append",
        dest="config_paths",
        default=default_config_paths,
        type=Path,
        help=(
            "Module config.yaml files to expand and lint recursively. "
            "Defaults to canonical entry modules."
        ),
    )
    parser.add_argument(
        "--strict-aliases",
        action="store_true",
        help="Treat deprecated model aliases as errors.",
    )
    parser.add_argument(
        "--strict-mixed-styles",
        action="store_true",
        help="Treat mixed report_template_section finding styles as errors.",
    )
    parser.add_argument(
        "--fail-on-warnings",
        action="store_true",
        help="Return non-zero exit code if warnings exist.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.paths and not args.config_paths:
        raise SystemExit("Provide at least one path or --config.")

    yaml_files, discovery_issues = discover_yaml_files(
        paths=args.paths,
        config_paths=args.config_paths,
    )

    lint_issues = lint_kb_yaml_files(
        yaml_files,
        strict_aliases=args.strict_aliases,
        strict_mixed_styles=args.strict_mixed_styles,
    )
    all_issues = [*discovery_issues, *lint_issues]

    for issue in all_issues:
        print(issue.format())

    summary = summarize_issues(all_issues)
    print(
        f"\nScanned {len(yaml_files)} YAML file(s): "
        f"{summary['errors']} error(s), {summary['warnings']} warning(s)."
    )

    if summary["errors"] > 0:
        return 1
    if args.fail_on_warnings and summary["warnings"] > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
