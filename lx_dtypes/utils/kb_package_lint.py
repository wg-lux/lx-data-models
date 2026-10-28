"""Package-scoped linting using the same loader and compiler as reporting clients."""

from __future__ import annotations

import warnings
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import yaml
from pydantic import ValidationError

from lx_dtypes.models.contracts.adapters import kb_to_core_concepts_payload
from lx_dtypes.models.interface.data_roots import module_search_root
from lx_dtypes.models.interface.DataLoader import DataLoader
from lx_dtypes.models.interface.KnowledgeBase import (
    KnowledgeBase,
    ReportTemplateConceptWarning,
)
from lx_dtypes.models.interface.KnowledgeBaseConfig import KnowledgeBaseConfig
from lx_dtypes.models.knowledge_base.report_template.TemplateReadiness import (
    ReportTemplateReadinessSummary,
)
from lx_dtypes.utils.kb_yaml_lint import (
    KbYamlLintIssue,
    discover_yaml_files,
    lint_kb_yaml_files,
    lint_name_version,
)


@dataclass(frozen=True)
class KbPackageCheck:
    knowledge_base: KnowledgeBase | None
    files: tuple[Path, ...]
    issues: tuple[KbYamlLintIssue, ...]


def lint_kb_package(
    config_path: Path, *, strict_aliases: bool = True, strict_mixed_styles: bool = True
) -> tuple[list[Path], list[KbYamlLintIssue]]:
    """Compatibility entry point for the CLI's source-located diagnostics."""
    result = check_kb_package(
        config_path,
        strict_aliases=strict_aliases,
        strict_mixed_styles=strict_mixed_styles,
    )
    return list(result.files), list(result.issues)


def check_kb_package(
    config_path: Path,
    *,
    strict_aliases: bool = True,
    strict_mixed_styles: bool = True,
    input_dirs: Sequence[Path] | None = None,
) -> KbPackageCheck:
    """Check one dependency closure, never merging independent package releases."""
    config_path = config_path.resolve()
    selected_configs: set[Path] = set()
    files, issues = discover_yaml_files(
        paths=[],
        config_paths=[config_path],
        resolved_configs=selected_configs,
        input_dirs=input_dirs,
    )
    issues.extend(
        lint_kb_yaml_files(
            files,
            strict_aliases=strict_aliases,
            strict_mixed_styles=strict_mixed_styles,
            check_authoring=True,
        )
    )
    if any(
        issue.severity == "error" and issue.code != "version_in_name"
        for issue in issues
    ):
        return KbPackageCheck(None, tuple(files), tuple(issues))

    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always", ReportTemplateConceptWarning)
        try:
            loader = DataLoader(
                input_dirs=list(input_dirs)
                if input_dirs is not None
                else [module_search_root(config_path)]
            )
            for path in sorted(selected_configs):
                selected = KnowledgeBaseConfig.from_yaml_file(path)
                issues.extend(
                    lint_name_version(selected.name, model_name="package", file=path)
                )
                loader.module_configs[selected.name] = selected
                loader.module_config_candidates.setdefault(selected.name, []).append(
                    selected
                )
            config = KnowledgeBaseConfig.from_yaml_file(config_path)
            kb = loader.load_knowledge_base(config.name)
        except (ValueError, TypeError, KeyError, OSError, yaml.YAMLError) as exc:
            issues.append(
                KbYamlLintIssue(
                    code="package_load_error",
                    severity="error",
                    file=config_path,
                    line=1,
                    column=1,
                    message=str(exc),
                )
            )
            kb = None
    for warning in captured:
        message = warning.message
        if isinstance(message, ReportTemplateConceptWarning):
            for definition in message.definitions or (message,):
                issues.append(
                    KbYamlLintIssue(
                        code="report_template_concept_definition",
                        severity="warning",
                        file=definition.source_file,
                        line=definition.line,
                        column=definition.column,
                        message=str(definition).removeprefix(
                            f"{definition.source_file}:{definition.line}:{definition.column}: "
                        ),
                    )
                )
        else:
            issues.append(
                KbYamlLintIssue(
                    code="runtime_warning",
                    severity="warning",
                    file=Path(warning.filename),
                    line=warning.lineno,
                    column=1,
                    message=str(message),
                )
            )
    if kb is None:
        return KbPackageCheck(None, tuple(files), tuple(issues))

    try:
        kb_to_core_concepts_payload(kb)
    except ValidationError as exc:
        issues.append(
            KbYamlLintIssue(
                code="invalid_knowledge_base",
                severity="error",
                file=config_path,
                line=1,
                column=1,
                message=str(exc),
            )
        )

    for name, template in sorted(kb.report_template.items()):
        source, source_line, source_column = kb.definition_source(
            "report_template", name
        ) or (template.source_file or config_path, 1, 1)
        try:
            payload = kb.export_report_template_preview(name)
            summary = ReportTemplateReadinessSummary.model_validate(
                payload["readiness"]
            )
        except (ValueError, TypeError, KeyError) as exc:
            issues.append(
                KbYamlLintIssue(
                    code="template_compile_error",
                    severity="error",
                    file=source,
                    line=source_line,
                    column=source_column,
                    message=f"Template '{name}' cannot compile: {exc}",
                )
            )
            continue
        for issue in summary.issues:
            if issue.severity == "info" and not issue.blocks_publish:
                continue
            model_names = {
                "template": ("report_template",),
                "section": ("report_template_section",),
                "finding": ("report_finding", "finding"),
                "examination": ("examination",),
                "validator": (
                    "findings_validator",
                    "examination_validator",
                    "classification_validator",
                    "intervention_validator",
                    "unit_validator",
                ),
                "registry": (),
            }[issue.scope]
            location = next(
                (
                    location
                    for model in model_names
                    if issue.reference
                    and (location := kb.definition_source(model, issue.reference))
                ),
                (source, source_line, source_column),
            )
            issues.append(
                KbYamlLintIssue(
                    code=issue.code,
                    severity="error"
                    if issue.blocks_publish or issue.severity == "blocking"
                    else "warning",
                    file=location[0],
                    line=location[1],
                    column=location[2],
                    message=issue.message,
                )
            )
    return KbPackageCheck(kb, tuple(files), tuple(issues))
