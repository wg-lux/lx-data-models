from __future__ import annotations

import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import ValidationError

from lx_dtypes.language import LANGUAGE_LABELS
from lx_dtypes.models.contracts.reference_catalog import ReferenceCatalogPayload
from lx_dtypes.models.interface.data_roots import module_search_root
from lx_dtypes.models.interface.DataLoader import DataLoader
from lx_dtypes.models.interface.KnowledgeBaseConfig import KnowledgeBaseConfig
from lx_dtypes.models.knowledge_base import knowledge_base_models_lookup
from lx_dtypes.utils.parser import (
    CLINICAL_CONCEPT_MODELS,
    _reject_duplicate_keys,
    camel_to_snake,
    normalize_model_name,
)
from lx_dtypes.utils.parser import (
    MODEL_NAME_ALIASES as MODEL_NAME_ALIASES,  # noqa: PLC0414 - Public re-export.
)

LintSeverity = Literal["error", "warning"]

# Runtime models and aliases are the authority for authoring tools too.
KNOWN_MODEL_NAMES = {camel_to_snake(name) for name in knowledge_base_models_lookup}


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
    payload: dict[str, Any]
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
        node = yaml.compose(raw_text)
        if node is not None:
            _reject_duplicate_keys(node, set())
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
        search_root = module_search_root(config_path).resolve()
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

    try:
        config = KnowledgeBaseConfig.from_yaml_file(config_path)
    except (ValueError, TypeError, OSError, yaml.YAMLError) as exc:
        return [], [
            _issue(
                code="invalid_config",
                severity="error",
                file=config_path,
                line=1,
                column=1,
                message=str(exc),
            )
        ]
    files = sorted(
        set(config.data.get_files_with_suffix(".yaml"))
        | set(config.data.get_files_with_suffix(".yml"))
    )
    directories = [*config.data.dirs, *([config.data.dir] if config.data.dir else [])]
    for directory in directories:
        if not directory.is_dir():
            issues.append(
                _issue(
                    code="missing_config_data_dir",
                    severity="warning",
                    file=config_path,
                    line=1,
                    column=1,
                    message=f"Configured data directory does not exist: {directory}",
                )
            )

    def _resolve_module_config(
        module_name: str,
    ) -> tuple[Path | None, list[KbYamlLintIssue]]:
        # Use runtime selection priorities; never pick the first ambiguous candidate.
        try:
            candidates = [
                KnowledgeBaseConfig.from_yaml_file(path)
                for path in sorted(set(module_index.get(module_name, [])))
            ]
            loader = DataLoader(
                input_dirs=[module_search_root(config_path)],
                module_config_candidates={module_name: candidates},
            )
            selected = loader.resolve_module_config(
                module_name,
                context_config=config,
                relation="module" if module_name in config.modules else "dependency",
            )
            return selected.source_file, []
        except (ValueError, TypeError, OSError, yaml.YAMLError) as exc:
            return None, [
                _issue(
                    code="module_resolution_error",
                    severity="error",
                    file=config_path,
                    line=1,
                    column=1,
                    message=str(exc),
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
    resolved_configs: set[Path] | None = None,
    input_dirs: Sequence[Path] | None = None,
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

    search_roots = sorted(
        {path.resolve() for path in input_dirs}
        if input_dirs is not None
        else {module_search_root(path.resolve()) for path in config_paths},
        key=lambda path: (len(path.parts), str(path)),
    )
    indexed_roots: list[Path] = []
    for search_root in search_roots:
        if any(search_root.is_relative_to(indexed) for indexed in indexed_roots):
            continue
        _extend_module_index(search_root)
        indexed_roots.append(search_root)

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
                    path, visited_configs=visited_configs
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

    if resolved_configs is not None:
        resolved_configs.update(visited_configs)
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

    def _find_duplicate_mapping_keys(node: yaml.Node) -> None:
        if isinstance(node, yaml.MappingNode):
            seen_keys: dict[tuple[str, str], yaml.Node] = {}
            for key_node, value_node in node.value:
                if isinstance(key_node, yaml.ScalarNode):
                    key_identity = (key_node.tag, key_node.value)
                    previous = seen_keys.get(key_identity)
                    if previous is not None:
                        issues.append(
                            _issue(
                                code="duplicate_mapping_key",
                                severity="error",
                                file=file_path,
                                line=int(key_node.start_mark.line) + 1,
                                column=int(key_node.start_mark.column) + 1,
                                message=(
                                    f"Duplicate YAML mapping key '{key_node.value}'; "
                                    "the earlier value at "
                                    f"{file_path}:{int(previous.start_mark.line) + 1}:"
                                    f"{int(previous.start_mark.column) + 1} would be "
                                    "silently overwritten by standard YAML loading."
                                ),
                            )
                        )
                    else:
                        seen_keys[key_identity] = key_node
                _find_duplicate_mapping_keys(value_node)
            return
        if isinstance(node, yaml.SequenceNode):
            for child_node in node.value:
                _find_duplicate_mapping_keys(child_node)

    _find_duplicate_mapping_keys(composed)

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


def _string_list(value: object) -> list[str]:
    if isinstance(value, str):
        token = value.strip()
        return [token] if token else []
    if not isinstance(value, list):
        return []
    return [
        token for item in value if isinstance(item, str) and (token := item.strip())
    ]


def _definition(
    items_by_definition: dict[tuple[str, str], _YamlItem],
    model: str,
    name: str,
) -> _YamlItem | None:
    return items_by_definition.get((model, name))


def _template_finding_names(
    items_by_definition: dict[tuple[str, str], _YamlItem],
) -> set[str]:
    template_finding_names: set[str] = set()
    for (model_name, _template_name), template_item in items_by_definition.items():
        if model_name != "report_template":
            continue
        for section_name in _string_list(template_item.payload.get("report_sections")):
            section_item = _definition(
                items_by_definition, "report_template_section", section_name
            )
            if section_item is None:
                continue
            raw_findings = section_item.payload.get("findings")
            if not isinstance(raw_findings, list):
                continue
            for raw_finding in raw_findings:
                if isinstance(raw_finding, dict):
                    finding_name = raw_finding.get("finding")
                    if isinstance(finding_name, str) and finding_name.strip():
                        template_finding_names.add(finding_name.strip())
                    continue
                if not isinstance(raw_finding, str) or not raw_finding.strip():
                    continue
                finding_ref = raw_finding.strip()
                report_finding_item = _definition(
                    items_by_definition, "report_finding", finding_ref
                )
                if report_finding_item is None:
                    template_finding_names.add(finding_ref)
                    continue
                finding_name = report_finding_item.payload.get("finding")
                if isinstance(finding_name, str) and finding_name.strip():
                    template_finding_names.add(finding_name.strip())
    return template_finding_names


def _lint_template_finding_descriptions(
    items_by_definition: dict[tuple[str, str], _YamlItem],
) -> list[KbYamlLintIssue]:
    issues: list[KbYamlLintIssue] = []
    for finding_name in sorted(_template_finding_names(items_by_definition)):
        finding_item = _definition(items_by_definition, "finding", finding_name)
        if finding_item is None:
            continue
        description = finding_item.payload.get("description")
        if isinstance(description, str) and description.strip():
            continue
        issues.append(
            _issue(
                code="template_finding_missing_description",
                severity="warning",
                file=finding_item.file,
                line=finding_item.line,
                column=finding_item.column,
                message=(
                    f"Finding '{finding_name}' is exposed by a report template "
                    "but has no non-empty description, so reporting clients "
                    "cannot explain the expected input."
                ),
            )
        )
    return issues


def _lint_classification_input_chains(
    definitions: dict[tuple[str, str], _DefinitionLocation],
    items_by_definition: dict[tuple[str, str], _YamlItem],
) -> list[KbYamlLintIssue]:
    issues: list[KbYamlLintIssue] = []
    for (
        model_name,
        classification_name,
    ), classification_item in items_by_definition.items():
        if model_name != "classification":
            continue

        choice_names = _string_list(
            classification_item.payload.get("classification_choices")
        )
        if not choice_names:
            issues.append(
                _issue(
                    code="classification_has_no_enterable_values",
                    severity="warning",
                    file=classification_item.file,
                    line=classification_item.line,
                    column=classification_item.column,
                    message=(
                        f"Classification '{classification_name}' has no "
                        "classification choices, so a rule requiring it cannot "
                        "be satisfied with an entered value."
                    ),
                )
            )
            continue

        for choice_name in choice_names:
            choice_item = _definition(
                items_by_definition, "classification_choice", choice_name
            )
            if choice_item is None:
                issues.append(
                    _issue(
                        code="missing_classification_choice_reference",
                        severity="warning",
                        file=classification_item.file,
                        line=classification_item.line,
                        column=classification_item.column,
                        message=(
                            f"Classification '{classification_name}' references "
                            f"missing classification choice '{choice_name}', "
                            "leaving that input path unusable."
                        ),
                    )
                )
                continue

            for descriptor_name in _string_list(
                choice_item.payload.get("classification_choice_descriptors")
            ):
                if (
                    "classification_choice_descriptor",
                    descriptor_name,
                ) in definitions:
                    continue
                issues.append(
                    _issue(
                        code="missing_choice_descriptor_reference",
                        severity="warning",
                        file=choice_item.file,
                        line=choice_item.line,
                        column=choice_item.column,
                        message=(
                            f"Classification choice '{choice_name}' references "
                            f"missing descriptor '{descriptor_name}', so its value "
                            "cannot be entered."
                        ),
                    )
                )
    return issues


def _candidate_coverage_choices(
    raw_concept: dict[object, object],
    selector: dict[object, object],
    classification_choices: set[str],
) -> set[str]:
    selected_choice = selector.get("classification_choice")
    if isinstance(selected_choice, str) and selected_choice:
        return {selected_choice}

    allowed_values = raw_concept.get("allowed_values")
    if not isinstance(allowed_values, list):
        return classification_choices
    matching_choices = {
        value
        for value in allowed_values
        if isinstance(value, str) and value in classification_choices
    }
    return matching_choices or classification_choices


def _descriptor_backed_choices(
    candidate_choices: set[str],
    items_by_definition: dict[tuple[str, str], _YamlItem],
) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for choice_name in sorted(candidate_choices):
        choice_item = _definition(
            items_by_definition, "classification_choice", choice_name
        )
        if choice_item is None:
            continue
        descriptor_names = _string_list(
            choice_item.payload.get("classification_choice_descriptors")
        )
        if descriptor_names:
            result[choice_name] = descriptor_names
    return result


def _lint_descriptor_coverage_paths(
    items_by_definition: dict[tuple[str, str], _YamlItem],
) -> list[KbYamlLintIssue]:
    issues: list[KbYamlLintIssue] = []

    # Coverage selectors evaluate classification_choice by default. Require an
    # explicit descriptor-value path when the selected choice is only a carrier
    # for numeric/text/boolean/selection descriptor input.
    for (model_name, template_name), template_item in items_by_definition.items():
        if model_name != "report_template":
            continue
        raw_concepts = template_item.payload.get("coverage_concepts")
        if not isinstance(raw_concepts, list):
            continue

        for raw_concept in raw_concepts:
            if not isinstance(raw_concept, dict):
                continue
            selector = raw_concept.get("finding_selector")
            if not isinstance(selector, dict):
                continue
            selector_classification_name = selector.get("classification_name")
            if (
                not isinstance(selector_classification_name, str)
                or not selector_classification_name
            ):
                continue

            selector_classification_item = _definition(
                items_by_definition,
                "classification",
                selector_classification_name,
            )
            if selector_classification_item is None:
                continue
            classification_choices = set(
                _string_list(
                    selector_classification_item.payload.get("classification_choices")
                )
            )
            candidate_choices = _candidate_coverage_choices(
                raw_concept, selector, classification_choices
            )
            descriptor_backed_choices = _descriptor_backed_choices(
                candidate_choices, items_by_definition
            )

            if not descriptor_backed_choices:
                continue

            value_path = _string_list(raw_concept.get("concept_value_path"))
            evaluates_descriptor_value = (
                "patient_finding_classification_choice_descriptors" in value_path
                and bool(value_path)
                and value_path[-1] == "descriptor_value"
            )
            if evaluates_descriptor_value:
                continue

            concept_id = raw_concept.get("concept_id", "<unnamed>")
            choice_summary = ", ".join(
                f"{choice} ({', '.join(descriptors)})"
                for choice, descriptors in descriptor_backed_choices.items()
            )
            issues.append(
                _issue(
                    code="incomplete_descriptor_value_rule",
                    severity="warning",
                    file=template_item.file,
                    line=template_item.line,
                    column=template_item.column,
                    message=(
                        f"Coverage concept '{concept_id}' in template "
                        f"'{template_name}' selects descriptor-backed choice(s) "
                        f"{choice_summary} for classification "
                        f"'{selector_classification_name}', but its value path "
                        "evaluates "
                        "only the choice token. The entered descriptor value "
                        "cannot be evaluated; set concept_value_path to the "
                        "choice descriptor's descriptor_value."
                    ),
                )
            )

    return issues


def _lint_incomplete_input_rules(
    definitions: dict[tuple[str, str], _DefinitionLocation],
    items_by_definition: dict[tuple[str, str], _YamlItem],
) -> list[KbYamlLintIssue]:
    """Find required input paths that cannot carry or evaluate a real value.

    A descriptor-backed classification has two semantic values: the selected
    classification-choice token and the descriptor value entered by the user.
    Coverage rules default to evaluating the choice token. Such a rule is
    incomplete when its selected choice owns descriptors but
    ``concept_value_path`` does not point at ``descriptor_value``.
    """

    return [
        *_lint_template_finding_descriptions(items_by_definition),
        *_lint_classification_input_chains(definitions, items_by_definition),
        *_lint_descriptor_coverage_paths(items_by_definition),
    ]


def _lint_unresolved_model_references(
    definitions: dict[tuple[str, str], _DefinitionLocation],
    items_by_definition: dict[tuple[str, str], _YamlItem],
) -> list[KbYamlLintIssue]:
    """Reject typed references that cannot be resolved in the discovered module graph.

    Descriptor units are validated by the runtime loader, but historically the
    lightweight YAML linter stopped after syntax and local input-chain checks.
    Keep this check model-aware so a literal such as ``unit: unknown`` cannot
    pass ``ok`` and then fail during ``KnowledgeBase`` construction.
    """

    issues: list[KbYamlLintIssue] = []
    for (model_name, descriptor_name), item in items_by_definition.items():
        if model_name != "classification_choice_descriptor":
            continue
        raw_unit = item.payload.get("unit")
        descriptor_type = item.payload.get("classification_choice_descriptor_type")
        if raw_unit is None and descriptor_type == "numeric":
            issues.append(
                _issue(
                    code="numeric_descriptor_missing_unit",
                    severity="error",
                    file=item.file,
                    line=item.line,
                    column=item.column,
                    message=(
                        f"Numeric classification choice descriptor "
                        f"'{descriptor_name}' omits 'unit'; the runtime default "
                        "would resolve to the sentinel 'unknown'. Define and "
                        "reference an explicit unit, including for dimensionless "
                        "counts."
                    ),
                )
            )
            continue
        if raw_unit is None:
            continue
        if not isinstance(raw_unit, str) or not raw_unit.strip():
            issues.append(
                _issue(
                    code="invalid_unit_reference",
                    severity="error",
                    file=item.file,
                    line=item.line,
                    column=item.column,
                    message=(
                        f"Classification choice descriptor '{descriptor_name}' "
                        "must reference a unit by a non-empty string name."
                    ),
                )
            )
            continue

        unit_name = raw_unit.strip()
        if ("unit", unit_name) in definitions:
            continue
        issues.append(
            _issue(
                code="missing_unit_reference",
                severity="error",
                file=item.file,
                line=item.line,
                column=item.column,
                message=(
                    f"Classification choice descriptor '{descriptor_name}' "
                    f"references missing unit '{unit_name}'. Define a unit with "
                    "that exact name in this module or one of its configured "
                    "dependencies."
                ),
            )
        )
    return issues


_VERSION_IN_NAME = re.compile(
    r"(?:^|[_-])v(?:ersion)?[_-]?\d+(?=$|[_.-])"
    r"|@\d+(?:[._-]\d+)*"
    r"|(?:^|[_-])\d+\.\d+\.\d+(?=$|[_-])"
    r"|(?:^|[_-])\d+_\d+_\d+(?=$|[_-])",
    re.IGNORECASE,
)
_DISPLAY_NAME_MODELS = (CLINICAL_CONCEPT_MODELS - {"reference_catalog"}) | {
    "report_template",
    "report_template_section",
}


def lint_name_version(
    name: str, *, model_name: str, file: Path, line: int = 1, column: int = 1
) -> list[KbYamlLintIssue]:
    issues: list[KbYamlLintIssue] = []
    if _VERSION_IN_NAME.search(name):
        issues.append(
            _issue(
                code="version_in_name",
                severity="error",
                file=file,
                line=line,
                column=column,
                message=f"'{model_name}' name '{name}' embeds a version. Keep names stable; "
                "use the package version (and report_template.version for templates). "
                "Update references together when correcting an unpublished identifier; "
                "do not rename published concepts in place.",
            )
        )
    return issues


def _lint_authoring_conventions(
    item: _YamlItem, model_name: str, name: str
) -> list[KbYamlLintIssue]:
    issues = lint_name_version(
        name, model_name=model_name, file=item.file, line=item.line, column=item.column
    )
    if model_name not in _DISPLAY_NAME_MODELS:
        return issues
    missing: list[str] = []
    for language in LANGUAGE_LABELS:
        fields = [f"name_{language}"]
        if model_name == "report_template_section":
            fields.insert(0, f"title_{language}")
        if not any(
            isinstance(value := item.payload.get(field), str)
            and value.strip()
            and (value.strip() != "unknown" or name == "unknown")
            for field in fields
        ):
            missing.append(" or ".join(fields))
    if missing:
        issues.append(
            _issue(
                code="missing_language_coverage",
                severity="warning",
                file=item.file,
                line=item.line,
                column=item.column,
                message=f"'{model_name}' '{name}' lacks authored display text: {', '.join(missing)}. "
                "Provide nonempty translations; identifier fallbacks and 'unknown' "
                "placeholders do not establish language coverage.",
            )
        )
    return issues


def lint_kb_yaml_files(
    yaml_files: Iterable[Path],
    *,
    strict_aliases: bool = False,
    strict_mixed_styles: bool = False,
    check_authoring: bool = False,
) -> list[KbYamlLintIssue]:
    issues: list[KbYamlLintIssue] = []
    definitions: dict[tuple[str, str], _DefinitionLocation] = {}
    items_by_definition: dict[tuple[str, str], _YamlItem] = {}

    for file_path in sorted({path.resolve() for path in yaml_files}):
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

            if check_authoring:
                issues.extend(
                    _lint_authoring_conventions(item, model_name, name.strip())
                )

            if model_name == "reference_catalog":
                try:
                    ReferenceCatalogPayload.model_validate(item.payload.get("payload"))
                except ValidationError as exc:
                    issues.append(
                        _issue(
                            code="invalid_reference_catalog",
                            severity="error",
                            file=item.file,
                            line=item.line,
                            column=item.column,
                            message=str(exc),
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
                items_by_definition[definition_key] = item

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

    issues.extend(_lint_incomplete_input_rules(definitions, items_by_definition))
    issues.extend(_lint_unresolved_model_references(definitions, items_by_definition))

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
