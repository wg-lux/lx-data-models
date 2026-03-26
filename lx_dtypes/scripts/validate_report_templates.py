from __future__ import annotations

import argparse
from pathlib import Path

from lx_dtypes.models.interface.DataLoader import DataLoader
from lx_dtypes.models.interface.ReportTemplateCompiler import ReportTemplateCompiler
from lx_dtypes.models.interface.ReportTemplateValidator import ReportTemplateValidator
from lx_dtypes.models.knowledge_base.report_template.TemplateReadiness import (
    ReportTemplateReadinessSummary,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate and compile report templates for release-quality checks."
    )
    parser.add_argument(
        "--data-root",
        type=Path,
        default=Path("lx_dtypes/data"),
        help="Root directory containing knowledge-base module config.yaml files.",
    )
    parser.add_argument(
        "--module",
        action="append",
        default=[],
        help="Module name to validate. Can be passed multiple times. Defaults to all discovered modules.",
    )
    parser.add_argument(
        "--fail-on-warning",
        action="store_true",
        help="Treat warnings on published templates as errors.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    loader = DataLoader(input_dirs=[args.data_root.resolve()])
    loader.load_module_configs()
    module_names = args.module or sorted(loader.module_configs.keys())

    has_failures = False
    for module_name in module_names:
        kb = loader.load_knowledge_base(module_name)
        validator = ReportTemplateValidator(
            kb=kb, compiler=ReportTemplateCompiler(kb=kb)
        )
        for template_name in sorted(kb.report_template.keys()):
            compiled = validator.validate_and_compile(template_name, mode="publish")
            summary = ReportTemplateReadinessSummary.model_validate(compiled["summary"])
            is_published = summary.lifecycle_status == "published"
            warning_failure = (
                args.fail_on_warning and is_published and summary.warning_issues
            )
            if is_published and not summary.can_publish:
                has_failures = True
            if warning_failure:
                has_failures = True

            print(
                f"{module_name}:{template_name} "
                f"status={summary.lifecycle_status} "
                f"readiness={summary.readiness} "
                f"blocking={summary.blocking_issues} "
                f"warnings={summary.warning_issues}"
            )
            for issue in summary.issues:
                print(
                    f"  - {issue.severity} {issue.scope} {issue.code}: {issue.message}"
                )

    return 1 if has_failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
