"""Package-scoped linting using the same loader and compiler as reporting clients."""

from __future__ import annotations

import warnings
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

import yaml
from pydantic import ValidationError

from lx_dtypes.knowledge_bases import (
    PackagedKnowledgeBaseCatalog,
    get_packaged_knowledge_base_catalog,
)
from lx_dtypes.models.contracts.adapters import kb_to_core_concepts_payload
from lx_dtypes.models.contracts.package_channel import LX_PACKAGE_MANIFEST_FILENAME
from lx_dtypes.models.contracts.package_kind import PackageKind
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
from lx_dtypes.package_archive import PackageArchiveError, verify_package_manifest
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
    package_kinds: Mapping[tuple[str, str], PackageKind] | None = None,
) -> KbPackageCheck:
    """Check one dependency closure, never merging independent package releases.

    Package kinds are the declared ``config.yaml`` kinds, completed by
    ``package_kinds`` (default: the installed catalog's reviewed kinds).
    """
    config_path = config_path.resolve()
    reviewed = (
        package_kinds
        if package_kinds is not None
        else _catalog_kinds(get_packaged_knowledge_base_catalog())
    )
    manifest_issues = _manifest_issues(config_path)
    selected_configs: set[Path] = set()
    files, issues = discover_yaml_files(
        paths=[],
        config_paths=[config_path],
        resolved_configs=selected_configs,
        input_dirs=input_dirs,
    )
    issues.extend(manifest_issues)
    issues.extend(
        lint_kb_yaml_files(
            files,
            strict_aliases=strict_aliases,
            strict_mixed_styles=strict_mixed_styles,
            check_authoring=True,
        )
    )
    # Authoring-quality errors do not prevent loading; structural errors do.
    if any(
        issue.severity == "error"
        and issue.code not in {"version_in_name", "missing_german_name"}
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
    issues.extend(
        _kind_issues(config_path, kb, input_dirs=input_dirs, reviewed=reviewed)
    )
    return KbPackageCheck(kb, tuple(files), tuple(issues))


def _catalog_kinds(
    catalog: PackagedKnowledgeBaseCatalog,
) -> dict[tuple[str, str], PackageKind]:
    return {
        (item.module_name, item.version): item.package_kind
        for item in catalog.knowledge_bases
        if item.package_kind is not None
    }


def _config_issue(config_path: Path, code: str, message: str) -> KbYamlLintIssue:
    return KbYamlLintIssue(
        code=code, severity="error", file=config_path, line=1, column=1, message=message
    )


def _manifest_issues(config_path: Path) -> list[KbYamlLintIssue]:
    """Typed kind and lx-package.json diagnostics read from the raw manifest."""
    try:
        content = config_path.read_bytes()
        raw = yaml.safe_load(content)
    except (OSError, yaml.YAMLError):
        return []  # Reported by YAML discovery as invalid_config_yaml.
    if not isinstance(raw, Mapping):
        return []
    issues: list[KbYamlLintIssue] = []
    kind = raw.get("package_kind")
    if kind is not None and kind not in {item.value for item in PackageKind}:
        issues.append(
            _config_issue(
                config_path,
                "invalid_package_kind",
                f"package_kind {kind!r} is not one of: "
                + ", ".join(item.value for item in PackageKind)
                + ".",
            )
        )
    manifest = config_path.parent / LX_PACKAGE_MANIFEST_FILENAME
    if manifest.is_file():
        try:
            verify_package_manifest(
                {
                    "config.yaml": content,
                    LX_PACKAGE_MANIFEST_FILENAME: manifest.read_bytes(),
                }
            )
        except PackageArchiveError as exc:
            issues.append(
                _config_issue(config_path, "package_manifest_mismatch", str(exc))
            )
    return issues


def _kind_issues(
    config_path: Path,
    kb: KnowledgeBase,
    *,
    input_dirs: Sequence[Path] | None,
    reviewed: Mapping[tuple[str, str], PackageKind],
) -> list[KbYamlLintIssue]:
    from lx_dtypes.package_kinds import (
        loaded_package_kind_findings,
        own_record_counts,
    )

    issues: list[KbYamlLintIssue] = []
    config = kb.config
    kind = config.package_kind or reviewed.get((config.name, config.version))
    if kind is PackageKind.study or kind is PackageKind.application_data:
        validators = sorted(
            name for name in own_record_counts(kb) if name.endswith("_validator")
        )
        if validators:
            issues.append(
                _config_issue(
                    config_path,
                    "validators_in_package_kind",
                    f"{kind.value} packages carry no validators; found "
                    + ", ".join(validators)
                    + ". Move them into a terminology or report_templates package.",
                )
            )
    try:
        findings = loaded_package_kind_findings(kb, package_kinds=reviewed)
    except ValueError as exc:
        return [*issues, _config_issue(config_path, "package_kind_conflict", str(exc))]
    issues.extend(
        _config_issue(
            config_path,
            "package_kind_dependency_violation",
            finding.format().removeprefix("violation: ")
            + " is not an allowed package-kind dependency.",
        )
        for finding in findings
        if finding.status == "violation"
    )
    return issues


def check_packaged_knowledge_bases(
    catalog: PackagedKnowledgeBaseCatalog | None = None,
) -> dict[tuple[str, str], KbPackageCheck]:
    """Lint every shipped release; unclassified releases are errors here."""
    selected = catalog if catalog is not None else get_packaged_knowledge_base_catalog()
    reviewed = _catalog_kinds(selected)
    results: dict[tuple[str, str], KbPackageCheck] = {}
    for descriptor in selected.knowledge_bases:
        module = descriptor.verified_resource_directory()
        if not isinstance(module, Path):
            raise TypeError(
                "Shipped packages must be installed as filesystem resources"
            )
        config_path = module / "config.yaml"
        result = check_kb_package(
            config_path,
            input_dirs=[descriptor.installed_data_root()],
            package_kinds=reviewed,
        )
        if (
            descriptor.package_kind is None
            and result.knowledge_base is not None
            and result.knowledge_base.config.package_kind is None
        ):
            result = KbPackageCheck(
                result.knowledge_base,
                result.files,
                (
                    *result.issues,
                    _config_issue(
                        config_path,
                        "unclassified_shipped_package",
                        f"{descriptor.module_name}@{descriptor.version} has "
                        "neither a declared nor a catalog package_kind.",
                    ),
                ),
            )
        results[(descriptor.module_name, descriptor.version)] = result
    return results
