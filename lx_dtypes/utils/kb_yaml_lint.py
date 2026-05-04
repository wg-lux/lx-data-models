from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Literal, Sequence

import yaml

LintSeverity = Literal["error", "warning"]

MODEL_NAME_ALIASES: dict[str, str] = {
    "finding_validator": "findings_validator",
}

KNOWN_MODEL_NAMES: set[str] = {
    "citation",
    "classification",
    "classification_type",
    "classification_choice",
    "classification_choice_descriptor",
    "examination",
    "examination_type",
    "finding",
    "finding_type",
    "indication",
    "indication_type",
    "intervention",
    "intervention_type",
    "unit",
    "unit_type",
    "information_source",
    "information_source_type",
    "report_template_section",
    "report_finding",
    "findings_validator",
    "examination_validator",
    "report_template",
}


def normalize_model_name(model_name: str) -> str:
    return MODEL_NAME_ALIASES.get(model_name, model_name)


@dataclass(frozen=True)
class KbYamlLintIssue:
    code: str
    severity: LintSeverity
    file: Path
    line: int
    column: int
    message: str

    def format(self) -> str:
        return (
            f"{self.severity.upper()} {self.file}:{self.line}:{self.column} "
            f"[{self.code}] {self.message}"
        )


@dataclass(frozen=True)
class _YamlItem:
    payload: Dict[str, Any]
    file: Path
    line: int
    column: int


@dataclass(frozen=True)
class _DefinitionLocation:
    file: Path
    line: int
    column: int


def _issue(
    *,
    code: str,
    severity: LintSeverity,
    file: Path,
    line: int,
    column: int,
    message: str,
) -> KbYamlLintIssue:
    return KbYamlLintIssue(
        code=code,
        severity=severity,
        file=file,
        line=line,
        column=column,
        message=message,
    )


def _discover_yaml_files_from_module_config(
    config_path: Path,
    *,
    module_index: dict[str, list[Path]] | None = None,
    visited_configs: set[Path] | None = None,
) -> tuple[list[Path], list[KbYamlLintIssue]]:
    config_path = config_path.resolve()
    issues: list[KbYamlLintIssue] = []
    if visited_configs is None:
        visited_configs = set()
    if config_path in visited_configs:
        return [], issues
    visited_configs.add(config_path)

    if not config_path.exists():
        return [], [
            _issue(
                code="missing_config",
                severity="error",
                file=config_path,
                line=1,
                column=1,
                message="Config file does not exist.",
            )
        ]

    raw_text = config_path.read_text(encoding="utf-8")
    try:
        loaded = yaml.safe_load(raw_text)
    except yaml.YAMLError as exc:
        problem_mark = getattr(exc, "problem_mark", None)
        line = int(problem_mark.line) + 1 if problem_mark is not None else 1
        column = int(problem_mark.column) + 1 if problem_mark is not None else 1
        return [], [
            _issue(
                code="invalid_config_yaml",
                severity="error",
                file=config_path,
                line=line,
                column=column,
                message=str(exc),
            )
        ]

    if not isinstance(loaded, dict):
        return [], [
            _issue(
                code="invalid_config_root",
                severity="error",
                file=config_path,
                line=1,
                column=1,
                message="Config YAML root must be a mapping.",
            )
        ]

    if module_index is None:
        search_root = config_path.parent.parent.resolve()
        module_index = {}
        for nested in sorted(search_root.rglob("config.yaml")):
            nested_resolved = nested.resolve()
            if nested_resolved == config_path:
                module_name = loaded.get("name")
                if isinstance(module_name, str) and module_name.strip():
                    module_index.setdefault(module_name.strip(), []).append(
                        nested_resolved
                    )
                continue

            nested_text = nested_resolved.read_text(encoding="utf-8")
            try:
                nested_loaded = yaml.safe_load(nested_text)
            except yaml.YAMLError:
                # Syntax issues in nested configs are reported once that module is linted.
                continue
            if not isinstance(nested_loaded, dict):
                continue
            module_name = nested_loaded.get("name")
            if isinstance(module_name, str) and module_name.strip():
                module_index.setdefault(module_name.strip(), []).append(nested_resolved)

    data = loaded.get("data")
    if data is None:
        # Aggregator modules can define only `modules`/`depends_on` without local YAML.
        files: list[Path] = []
    elif not isinstance(data, dict):
        return [], [
            _issue(
                code="missing_config_data",
                severity="error",
                file=config_path,
                line=1,
                column=1,
                message="Config YAML must define a mapping under key 'data'.",
            )
        ]
    else:
        base_dir = config_path.parent
        files = []

        configured_files = data.get("files", [])
        if isinstance(configured_files, list):
            for rel_path in configured_files:
                if not isinstance(rel_path, str):
                    continue
                file_path = (base_dir / rel_path).resolve()
                if file_path.suffix in {".yaml", ".yml"}:
                    files.append(file_path)

        configured_dirs = data.get("dirs", [])
        if isinstance(configured_dirs, list):
            for rel_dir in configured_dirs:
                if not isinstance(rel_dir, str):
                    continue
                dir_path = (base_dir / rel_dir).resolve()
                if not dir_path.exists():
                    issues.append(
                        _issue(
                            code="missing_config_data_dir",
                            severity="warning",
                            file=config_path,
                            line=1,
                            column=1,
                            message=(
                                f"Configured data directory does not exist: {dir_path}"
                            ),
                        )
                    )
                    continue
                files.extend(sorted(dir_path.rglob("*.yaml")))
                files.extend(sorted(dir_path.rglob("*.yml")))

    def _resolve_module_config(
        module_name: str,
    ) -> tuple[Path | None, list[KbYamlLintIssue]]:
        candidates = sorted(set(module_index.get(module_name, [])))
        if not candidates:
            return None, [
                _issue(
                    code="missing_config_module",
                    severity="warning",
                    file=config_path,
                    line=1,
                    column=1,
                    message=f"Referenced module '{module_name}' has no config.yaml.",
                )
            ]
        if len(candidates) == 1:
            return candidates[0], []

        visited_matches = [c for c in candidates if c in visited_configs]
        if visited_matches:
            selected = sorted(visited_matches)[0]
            return selected, []

        current_group = config_path.parent.parent.resolve()
        same_group = [
            c for c in candidates if c.parent.parent.resolve() == current_group
        ]
        if len(same_group) == 1:
            return same_group[0], []

        selected = same_group[0] if same_group else candidates[0]
        return selected, [
            _issue(
                code="ambiguous_module_config",
                severity="warning",
                file=config_path,
                line=1,
                column=1,
                message=(
                    f"Module '{module_name}' is defined in multiple configs; "
                    f"selected '{selected}'."
                ),
            )
        ]

    referenced_modules: list[str] = []
    for key in ("depends_on", "modules"):
        raw_modules = loaded.get(key, [])
        if not isinstance(raw_modules, list):
            continue
        for entry in raw_modules:
            if isinstance(entry, str) and entry.strip():
                referenced_modules.append(entry.strip())

    for module_name in referenced_modules:
        module_config_path, resolution_issues = _resolve_module_config(module_name)
        issues.extend(resolution_issues)
        if module_config_path is None:
            continue
        nested_files, nested_issues = _discover_yaml_files_from_module_config(
            module_config_path,
            module_index=module_index,
            visited_configs=visited_configs,
        )
        files.extend(nested_files)
        issues.extend(nested_issues)

    deduped: list[Path] = []
    seen: set[Path] = set()
    for file_path in files:
        resolved = file_path.resolve()
        if resolved not in seen:
            seen.add(resolved)
            deduped.append(resolved)

    return deduped, issues


def discover_yaml_files(
    *,
    paths: Sequence[Path],
    config_paths: Sequence[Path],
) -> tuple[list[Path], list[KbYamlLintIssue]]:
    issues: list[KbYamlLintIssue] = []
    files: list[Path] = []
    visited_configs: set[Path] = set()
    module_index: dict[str, list[Path]] = {}

    def _extend_module_index(search_root: Path) -> None:
        for nested in sorted(search_root.rglob("config.yaml")):
            nested_resolved = nested.resolve()
            nested_text = nested_resolved.read_text(encoding="utf-8")
            try:
                nested_loaded = yaml.safe_load(nested_text)
            except yaml.YAMLError:
                continue
            if not isinstance(nested_loaded, dict):
                continue
            module_name = nested_loaded.get("name")
            if isinstance(module_name, str) and module_name.strip():
                module_index.setdefault(module_name.strip(), []).append(nested_resolved)

    for config_path in config_paths:
        _extend_module_index(config_path.resolve().parent.parent)

    for config_path in config_paths:
        discovered, config_issues = _discover_yaml_files_from_module_config(
            config_path,
            module_index=module_index,
            visited_configs=visited_configs,
        )
        files.extend(discovered)
        issues.extend(config_issues)

    for path in paths:
        if not path.exists():
            issues.append(
                _issue(
                    code="missing_path",
                    severity="error",
                    file=path,
                    line=1,
                    column=1,
                    message="Path does not exist.",
                )
            )
            continue

        if path.is_file():
            if path.name == "config.yaml":
                discovered, config_issues = _discover_yaml_files_from_module_config(
                    path
                )
                files.extend(discovered)
                issues.extend(config_issues)
                continue
            if path.suffix in {".yaml", ".yml"}:
                files.append(path.resolve())
            continue

        files.extend(
            sorted(
                file_path.resolve()
                for file_path in path.rglob("*.yaml")
                if file_path.name != "config.yaml"
            )
        )
        files.extend(
            sorted(
                file_path.resolve()
                for file_path in path.rglob("*.yml")
                if file_path.name != "config.yaml"
            )
        )

    deduped: list[Path] = []
    seen: set[Path] = set()
    for file_path in files:
        if file_path not in seen:
            seen.add(file_path)
            deduped.append(file_path)

    return deduped, issues


def _load_yaml_items(file_path: Path) -> tuple[list[_YamlItem], list[KbYamlLintIssue]]:
    issues: list[KbYamlLintIssue] = []
    raw_text = file_path.read_text(encoding="utf-8")
    try:
        loaded = yaml.safe_load(raw_text)
    except yaml.YAMLError as exc:
        problem_mark = getattr(exc, "problem_mark", None)
        line = int(problem_mark.line) + 1 if problem_mark is not None else 1
        column = int(problem_mark.column) + 1 if problem_mark is not None else 1
        issues.append(
            _issue(
                code="invalid_yaml",
                severity="error",
                file=file_path,
                line=line,
                column=column,
                message=str(exc),
            )
        )
        return [], issues

    if loaded is None:
        return [], issues

    if not isinstance(loaded, list):
        issues.append(
            _issue(
                code="invalid_root_type",
                severity="error",
                file=file_path,
                line=1,
                column=1,
                message="YAML root must be a list of records and therefore start with a -.",
            )
        )
        return [], issues

    try:
        composed = yaml.compose(raw_text)
    except yaml.YAMLError as exc:
        problem_mark = getattr(exc, "problem_mark", None)
        line = int(problem_mark.line) + 1 if problem_mark is not None else 1
        column = int(problem_mark.column) + 1 if problem_mark is not None else 1
        issues.append(
            _issue(
                code="invalid_yaml",
                severity="error",
                file=file_path,
                line=line,
                column=column,
                message=str(exc),
            )
        )
        return [], issues

    if composed is None:
        return [], issues

    if not isinstance(composed, yaml.SequenceNode):
        issues.append(
            _issue(
                code="invalid_root_type",
                severity="error",
                file=file_path,
                line=1,
                column=1,
                message="YAML root must be a sequence node.",
            )
        )
        return [], issues

    items: list[_YamlItem] = []
    for idx, raw_item in enumerate(loaded):
        node = composed.value[idx] if idx < len(composed.value) else None
        line = int(node.start_mark.line) + 1 if node is not None else 1
        column = int(node.start_mark.column) + 1 if node is not None else 1
        if not isinstance(raw_item, dict):
            issues.append(
                _issue(
                    code="invalid_item_type",
                    severity="error",
                    file=file_path,
                    line=line,
                    column=column,
                    message="Each list entry must be a mapping.",
                )
            )
            continue
        items.append(
            _YamlItem(
                payload=dict(raw_item),
                file=file_path,
                line=line,
                column=column,
            )
        )
    return items, issues


def lint_kb_yaml_files(
    yaml_files: Iterable[Path],
    *,
    strict_aliases: bool = False,
    strict_mixed_styles: bool = False,
) -> list[KbYamlLintIssue]:
    issues: list[KbYamlLintIssue] = []
    definitions: dict[tuple[str, str], _DefinitionLocation] = {}

    for file_path in sorted(set(path.resolve() for path in yaml_files)):
        if not file_path.exists():
            issues.append(
                _issue(
                    code="missing_file",
                    severity="error",
                    file=file_path,
                    line=1,
                    column=1,
                    message="YAML file does not exist.",
                )
            )
            continue

        yaml_items, load_issues = _load_yaml_items(file_path)
        issues.extend(load_issues)

        for item in yaml_items:
            model_raw = item.payload.get("model")
            if not isinstance(model_raw, str) or model_raw.strip() == "":
                issues.append(
                    _issue(
                        code="missing_model",
                        severity="error",
                        file=item.file,
                        line=item.line,
                        column=item.column,
                        message="Record must include a non-empty string in field 'model'.",
                    )
                )
                continue

            model_name = normalize_model_name(model_raw.strip())
            if model_name != model_raw.strip():
                issues.append(
                    _issue(
                        code="alias_model_name",
                        severity="error" if strict_aliases else "warning",
                        file=item.file,
                        line=item.line,
                        column=item.column,
                        message=(
                            f"Model alias '{model_raw}' is deprecated; "
                            f"use '{model_name}'."
                        ),
                    )
                )

            if model_name not in KNOWN_MODEL_NAMES:
                issues.append(
                    _issue(
                        code="unknown_model",
                        severity="error",
                        file=item.file,
                        line=item.line,
                        column=item.column,
                        message=f"Unknown model '{model_raw}'.",
                    )
                )
                continue

            name = item.payload.get("name")
            if not isinstance(name, str) or name.strip() == "":
                issues.append(
                    _issue(
                        code="missing_name",
                        severity="error",
                        file=item.file,
                        line=item.line,
                        column=item.column,
                        message="Record must include a non-empty string in field 'name'.",
                    )
                )
                continue

            definition_key = (model_name, name.strip())
            existing = definitions.get(definition_key)
            if existing is not None:
                issues.append(
                    _issue(
                        code="duplicate_name",
                        severity="error",
                        file=item.file,
                        line=item.line,
                        column=item.column,
                        message=(
                            f"Duplicate '{model_name}' name '{name.strip()}'; "
                            f"previously defined at "
                            f"{existing.file}:{existing.line}:{existing.column}."
                        ),
                    )
                )
            else:
                definitions[definition_key] = _DefinitionLocation(
                    file=item.file,
                    line=item.line,
                    column=item.column,
                )

            if model_name != "report_template_section":
                continue

            findings = item.payload.get("findings", [])
            if not isinstance(findings, list):
                continue

            has_string_ref = any(isinstance(value, str) for value in findings)
            has_mapping_ref = any(isinstance(value, dict) for value in findings)
            if has_string_ref and has_mapping_ref:
                issues.append(
                    _issue(
                        code="mixed_finding_reference_styles",
                        severity="error" if strict_mixed_styles else "warning",
                        file=item.file,
                        line=item.line,
                        column=item.column,
                        message=(
                            "Section uses mixed finding reference styles "
                            "(string and inline object). Prefer one style."
                        ),
                    )
                )

    issues.sort(
        key=lambda issue: (
            str(issue.file),
            issue.line,
            issue.column,
            0 if issue.severity == "error" else 1,
            issue.code,
        )
    )
    return issues


def summarize_issues(issues: Sequence[KbYamlLintIssue]) -> dict[str, int]:
    errors = sum(1 for issue in issues if issue.severity == "error")
    warnings = sum(1 for issue in issues if issue.severity == "warning")
    return {"errors": errors, "warnings": warnings}
