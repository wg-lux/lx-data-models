#!/usr/bin/env python3
"""Lint KB concept YAML files with explicit source locations."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from lx_dtypes.utils.kb_yaml_lint import (  # noqa: E402
    discover_yaml_files,
    lint_kb_yaml_files,
    summarize_issues,
)


def parse_args() -> argparse.Namespace:
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
        help=(
            "YAML files or directories to lint. If a path is 'config.yaml', "
            "its configured data files/dirs are linted."
        ),
    )
    parser.add_argument(
        "--config",
        action="append",
        dest="config_paths",
        default=[],
        type=Path,
        help="Additional module config.yaml files to expand and lint.",
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
