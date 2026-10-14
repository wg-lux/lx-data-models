#!/usr/bin/env python3
"""Lint KB concept YAML files with explicit source locations."""

from __future__ import annotations

import argparse
from pathlib import Path

from lx_dtypes.models.interface.data_roots import package_data_root
from lx_dtypes.utils.kb_package_lint import lint_kb_package
from lx_dtypes.utils.kb_yaml_lint import (
    KbYamlLintIssue,
    discover_yaml_files,
    lint_kb_yaml_files,
    summarize_issues,
)
from lx_dtypes.utils.parser import parse_shallow_object_with_meta


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
        default=[],
        help=(
            "YAML files or directories to lint. If omitted, current shipped package "
            "configs are linted. If a path is 'config.yaml', its configured "
            "data files/dirs (including dependencies/modules) are linted."
        ),
    )
    parser.add_argument(
        "--config",
        action="append",
        dest="config_paths",
        default=[],
        type=Path,
        help=(
            "Module config.yaml files to expand and lint recursively. "
            "May be repeated. When neither paths nor --config are supplied, "
            "the current shipped packages (excluding historical releases) are linted."
        ),
    )
    parser.add_argument(
        "--strict-aliases",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Treat deprecated model aliases as errors.",
    )
    parser.add_argument(
        "--strict-mixed-styles",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Treat mixed report_template_section finding styles as errors.",
    )
    parser.add_argument(
        "--fail-on-warnings",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Return non-zero exit code if warnings exist.",
    )
    args = parser.parse_args()
    if not args.paths and not args.config_paths:
        args.config_paths = sorted(
            path
            for category in ("terminology", "report_templates")
            for path in (package_data_root() / category).rglob("config.yaml")
            if "versions" not in path.relative_to(package_data_root()).parts
        )
    return args


def main() -> int:
    args = parse_args()
    if not args.paths and not args.config_paths:
        raise SystemExit("Provide at least one path or --config.")

    configs = set(args.config_paths)
    raw_paths: list[Path] = []
    for path in args.paths:
        if path.name == "config.yaml":
            configs.add(path)
        elif path.is_dir() and (manifests := list(path.rglob("config.yaml"))):
            configs.update(manifests)
        else:
            raw_paths.append(path)

    yaml_files: set[Path] = set()
    all_issues: list[KbYamlLintIssue] = []
    configs = {path.resolve() for path in configs}
    if configs:
        print(f"Checking {len(configs)} package(s)...", flush=True)
    for config in sorted(configs):
        files, issues = lint_kb_package(
            config,
            strict_aliases=args.strict_aliases,
            strict_mixed_styles=args.strict_mixed_styles,
        )
        yaml_files.update(files)
        all_issues.extend(issues)
    if raw_paths:
        files, issues = discover_yaml_files(paths=raw_paths, config_paths=[])
        if not files and not issues:
            issues.append(
                KbYamlLintIssue(
                    code="no_yaml_files",
                    severity="error",
                    file=raw_paths[0],
                    line=1,
                    column=1,
                    message="Selection contains no YAML records or package manifests.",
                )
            )
        yaml_files.update(files)
        issues.extend(
            lint_kb_yaml_files(
                files,
                strict_aliases=args.strict_aliases,
                strict_mixed_styles=args.strict_mixed_styles,
                check_authoring=True,
            )
        )
        for file in files:
            try:
                parse_shallow_object_with_meta(
                    file, strict_model_aliases=args.strict_aliases
                )
            except (ValueError, TypeError, OSError) as exc:
                issues.append(
                    KbYamlLintIssue(
                        code="invalid_model",
                        severity="error",
                        file=file,
                        line=1,
                        column=1,
                        message=str(exc),
                    )
                )
        all_issues.extend(issues)
        print(
            "File-only checks: use --config for dependency and template readiness validation."
        )
    all_issues = sorted(
        set(all_issues),
        key=lambda issue: (
            str(issue.file),
            issue.line,
            issue.column,
            issue.code,
            issue.message,
        ),
    )
    print(
        f"Checked {len(configs)} package(s), including dependency loading and template readiness."
    )

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
