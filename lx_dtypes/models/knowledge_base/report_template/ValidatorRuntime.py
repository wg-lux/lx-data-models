from __future__ import annotations

from typing import Any, Dict, List, Literal, Mapping, Sequence, TypedDict

from .ExaminationValidator import ExaminationValidator
from .FindingsValidator import (
    FindingsValidator,
    FindingsValidatorCondition,
    FindingsValidatorConditionClause,
)
from .ReportTemplate import ReportTemplate


class RuntimeValidationIssueDataDict(TypedDict, total=False):
    code: str
    level: Literal["error", "warning"]
    message: str
    validator_name: str
    validator_kind: Literal["findings_validator", "examination_validator", "template"]
    details: Dict[str, Any]


class ExaminationValidatorDependencyStatusDataDict(TypedDict):
    name: str
    ok: bool


class FindingsValidatorExecutionDataDict(TypedDict):
    name: str
    ok: bool
    operator: str
    finding: str
    matched_occurrences: int
    triggered_occurrences: int
    missing_required_classifications: List[str]
    issues: List[RuntimeValidationIssueDataDict]


class ExaminationValidatorExecutionDataDict(TypedDict):
    name: str
    ok: bool
    finding_validator_status: List[ExaminationValidatorDependencyStatusDataDict]
    examination_validator_status: List[ExaminationValidatorDependencyStatusDataDict]
    issues: List[RuntimeValidationIssueDataDict]


class ReportTemplateRuntimeValidationResultDataDict(TypedDict):
    template_name: str
    ok: bool
    evaluated_findings_count: int
    findings_validators: List[FindingsValidatorExecutionDataDict]
    examination_validators: List[ExaminationValidatorExecutionDataDict]
    issues: List[RuntimeValidationIssueDataDict]


class _RuntimeFindingOccurrence(TypedDict):
    finding: str
    classifications: Dict[str, List[Any]]


def _as_str_list(value: Any) -> List[str]:
    if value in (None, ""):
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, Sequence):
        result: List[str] = []
        for item in value:
            token = _normalize_identifier(item)
            if token:
                result.append(token)
        return result
    token = _normalize_identifier(value)
    return [token] if token else []


def _normalize_identifier(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (int, float, bool)):
        return str(value)
    if isinstance(value, Mapping):
        for key in ("name", "key", "slug", "id", "pk", "value"):
            if key in value:
                token = _normalize_identifier(value.get(key))
                if token:
                    return token
        return ""
    return str(value).strip()


def _extract_classification_value(payload: Mapping[str, Any]) -> Any:
    for key in ("value", "classification_choice", "classificationChoice", "choice"):
        if key in payload:
            return payload.get(key)
    if "values" in payload:
        values = payload.get("values")
        if isinstance(values, list):
            return values
    return None


def _add_classification_value(
    target: Dict[str, List[Any]], classification_name: Any, value: Any
) -> None:
    normalized_name = _normalize_identifier(classification_name)
    if not normalized_name:
        return

    bucket = target.setdefault(normalized_name, [])
    if isinstance(value, list):
        for item in value:
            if item is not None:
                bucket.append(item)
        return
    if value is not None:
        bucket.append(value)
        return
    # If no explicit value exists, still mark the classification as present.
    bucket.append(True)


def _normalize_classifications(raw: Any) -> Dict[str, List[Any]]:
    normalized: Dict[str, List[Any]] = {}
    if raw is None:
        return normalized

    if isinstance(raw, Mapping):
        for class_name, class_value in raw.items():
            _add_classification_value(normalized, class_name, class_value)
        return normalized

    if not isinstance(raw, list):
        return normalized

    for item in raw:
        if isinstance(item, Mapping):
            classification_name = item.get("classification")
            if classification_name is None:
                classification_name = item.get("name")
            if classification_name is None:
                classification_name = item.get("key")
            class_value = _extract_classification_value(item)
            _add_classification_value(normalized, classification_name, class_value)
            continue

        _add_classification_value(normalized, item, True)

    return normalized


def _normalize_reported_findings(
    reported_findings: Sequence[Mapping[str, Any]] | None,
) -> List[_RuntimeFindingOccurrence]:
    if not reported_findings:
        return []

    occurrences: List[_RuntimeFindingOccurrence] = []
    for finding_payload in reported_findings:
        if not isinstance(finding_payload, Mapping):
            continue

        finding_name = _normalize_identifier(finding_payload.get("finding"))
        if not finding_name:
            finding_name = _normalize_identifier(finding_payload.get("name"))
        if not finding_name:
            continue

        occurrences.append(
            _RuntimeFindingOccurrence(
                finding=finding_name,
                classifications=_normalize_classifications(
                    finding_payload.get("classifications")
                ),
            )
        )

    return occurrences


def _coerce_numeric(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        token = value.strip()
        if token == "":
            return None
        try:
            return float(token)
        except ValueError:
            return None
    return None


def _value_equals(left: Any, right: Any) -> bool:
    if left == right:
        return True

    left_num = _coerce_numeric(left)
    right_num = _coerce_numeric(right)
    if left_num is not None and right_num is not None:
        return left_num == right_num

    return str(left) == str(right)


def _compare_ordered(left: Any, right: Any, operator: str) -> bool:
    left_num = _coerce_numeric(left)
    right_num = _coerce_numeric(right)

    if left_num is not None and right_num is not None:
        if operator == "gt":
            return left_num > right_num
        if operator == "gte":
            return left_num >= right_num
        if operator == "lt":
            return left_num < right_num
        if operator == "lte":
            return left_num <= right_num
        return False

    left_text = str(left)
    right_text = str(right)
    if operator == "gt":
        return left_text > right_text
    if operator == "gte":
        return left_text >= right_text
    if operator == "lt":
        return left_text < right_text
    if operator == "lte":
        return left_text <= right_text
    return False


def _evaluate_clause(
    clause: FindingsValidatorConditionClause, classifications: Mapping[str, List[Any]]
) -> bool:
    actual_values = classifications.get(clause.classification, [])
    if not actual_values:
        return False

    comparator = clause.comparator
    if comparator == "eq":
        return any(_value_equals(value, clause.value) for value in actual_values)
    if comparator == "ne":
        return all(not _value_equals(value, clause.value) for value in actual_values)
    if comparator in {"gt", "gte", "lt", "lte"}:
        return any(
            _compare_ordered(value, clause.value, comparator) for value in actual_values
        )

    expected_values = clause.values or []
    if clause.value is not None and not expected_values:
        expected_values = [clause.value]
    if not expected_values:
        return False

    if comparator == "in":
        return any(
            any(_value_equals(value, expected) for expected in expected_values)
            for value in actual_values
        )
    if comparator == "not_in":
        return all(
            not any(_value_equals(value, expected) for expected in expected_values)
            for value in actual_values
        )
    return False


def _condition_matches(
    condition: FindingsValidatorCondition, classifications: Mapping[str, List[Any]]
) -> bool:
    any_clauses = list(condition.any or [])
    all_clauses = list(condition.all or [])

    any_match = True
    if any_clauses:
        any_match = any(_evaluate_clause(clause, classifications) for clause in any_clauses)

    all_match = True
    if all_clauses:
        all_match = all(_evaluate_clause(clause, classifications) for clause in all_clauses)

    return any_match and all_match


def _missing_required_classifications(
    condition: FindingsValidatorCondition, classifications: Mapping[str, List[Any]]
) -> List[str]:
    missing: List[str] = []
    for requirement in condition.then_requires or []:
        if isinstance(requirement, Mapping):
            class_name = _normalize_identifier(requirement.get("classification"))
        else:
            class_name = _normalize_identifier(
                getattr(requirement, "classification", None)
            )
        if not class_name:
            continue
        if not classifications.get(class_name):
            missing.append(class_name)
    return missing


def _build_issue(
    *,
    code: str,
    message: str,
    validator_name: str,
    validator_kind: Literal["findings_validator", "examination_validator", "template"],
    level: Literal["error", "warning"] = "error",
    details: Dict[str, Any] | None = None,
) -> RuntimeValidationIssueDataDict:
    issue = RuntimeValidationIssueDataDict(
        code=code,
        level=level,
        message=message,
        validator_name=validator_name,
        validator_kind=validator_kind,
    )
    if details is not None:
        issue["details"] = details
    return issue


def evaluate_findings_validator_runtime(
    validator: FindingsValidator,
    *,
    reported_findings: Sequence[Mapping[str, Any]] | None = None,
) -> FindingsValidatorExecutionDataDict:
    normalized_findings = _normalize_reported_findings(reported_findings)
    target_finding = validator.finding
    matched_occurrences = [
        finding for finding in normalized_findings if finding["finding"] == target_finding
    ]

    issues: List[RuntimeValidationIssueDataDict] = []
    missing_required_classifications: List[str] = []
    triggered_occurrences = 0

    if validator.operator == "exists":
        ok = len(matched_occurrences) > 0
        if not ok:
            issues.append(
                _build_issue(
                    code="finding_not_present",
                    message=(
                        f"Finding '{target_finding}' is required by validator "
                        f"'{validator.name}' but is not present."
                    ),
                    validator_name=validator.name,
                    validator_kind="findings_validator",
                )
            )
    elif validator.operator == "missing":
        ok = len(matched_occurrences) == 0
        if not ok:
            issues.append(
                _build_issue(
                    code="finding_present_but_should_be_missing",
                    message=(
                        f"Finding '{target_finding}' should be absent for validator "
                        f"'{validator.name}'."
                    ),
                    validator_name=validator.name,
                    validator_kind="findings_validator",
                    details={"matched_occurrences": len(matched_occurrences)},
                )
            )
    elif validator.operator == "conditional":
        condition = validator.query.condition
        if condition is None:
            ok = False
            issues.append(
                _build_issue(
                    code="invalid_conditional_validator_definition",
                    message=(
                        f"Validator '{validator.name}' uses 'conditional' operator but "
                        "has no condition block."
                    ),
                    validator_name=validator.name,
                    validator_kind="findings_validator",
                )
            )
        else:
            for occurrence_index, occurrence in enumerate(matched_occurrences):
                if not _condition_matches(condition, occurrence["classifications"]):
                    continue
                triggered_occurrences += 1
                missing = _missing_required_classifications(
                    condition, occurrence["classifications"]
                )
                if not missing:
                    continue
                missing_required_classifications.extend(missing)
                issues.append(
                    _build_issue(
                        code="missing_required_classification",
                        message=(
                            f"Validator '{validator.name}' requires classification(s) "
                            f"{', '.join(missing)} when condition is met."
                        ),
                        validator_name=validator.name,
                        validator_kind="findings_validator",
                        details={
                            "occurrence_index": occurrence_index,
                            "missing_classifications": missing,
                        },
                    )
                )
            ok = len(issues) == 0
    else:
        ok = False
        issues.append(
            _build_issue(
                code="unsupported_findings_validator_operator",
                message=(
                    f"Operator '{validator.operator}' is not supported by the runtime "
                    "validator engine."
                ),
                validator_name=validator.name,
                validator_kind="findings_validator",
            )
        )

    dedup_missing = sorted(set(missing_required_classifications))
    return FindingsValidatorExecutionDataDict(
        name=validator.name,
        ok=ok,
        operator=validator.operator,
        finding=target_finding,
        matched_occurrences=len(matched_occurrences),
        triggered_occurrences=triggered_occurrences,
        missing_required_classifications=dedup_missing,
        issues=issues,
    )


def evaluate_report_template_validators_runtime(
    template: ReportTemplate,
    *,
    findings_validators: Mapping[str, FindingsValidator],
    examination_validators: Mapping[str, ExaminationValidator],
    reported_findings: Sequence[Mapping[str, Any]] | None = None,
) -> ReportTemplateRuntimeValidationResultDataDict:
    normalized_findings = _normalize_reported_findings(reported_findings)

    findings_cache: Dict[str, FindingsValidatorExecutionDataDict] = {}
    exam_cache: Dict[str, ExaminationValidatorExecutionDataDict] = {}

    def evaluate_finding_validator_by_name(
        validator_name: str,
    ) -> FindingsValidatorExecutionDataDict:
        cached = findings_cache.get(validator_name)
        if cached is not None:
            return cached

        validator = findings_validators.get(validator_name)
        if validator is None:
            result = FindingsValidatorExecutionDataDict(
                name=validator_name,
                ok=False,
                operator="unknown",
                finding="unknown",
                matched_occurrences=0,
                triggered_occurrences=0,
                missing_required_classifications=[],
                issues=[
                    _build_issue(
                        code="unknown_findings_validator_reference",
                        message=(
                            f"Findings validator '{validator_name}' is referenced but "
                            "is not defined."
                        ),
                        validator_name=validator_name,
                        validator_kind="findings_validator",
                    )
                ],
            )
            findings_cache[validator_name] = result
            return result

        result = evaluate_findings_validator_runtime(
            validator, reported_findings=normalized_findings
        )
        findings_cache[validator_name] = result
        return result

    def evaluate_examination_validator_by_name(
        validator_name: str,
        stack: List[str],
    ) -> ExaminationValidatorExecutionDataDict:
        cached = exam_cache.get(validator_name)
        if cached is not None:
            return cached

        if validator_name in stack:
            cycle = [*stack, validator_name]
            return ExaminationValidatorExecutionDataDict(
                name=validator_name,
                ok=False,
                finding_validator_status=[],
                examination_validator_status=[],
                issues=[
                    _build_issue(
                        code="circular_examination_validator_dependency",
                        message=(
                            f"Circular examination-validator dependency detected: "
                            f"{' -> '.join(cycle)}"
                        ),
                        validator_name=validator_name,
                        validator_kind="examination_validator",
                        details={"cycle": cycle},
                    )
                ],
            )

        validator = examination_validators.get(validator_name)
        if validator is None:
            result = ExaminationValidatorExecutionDataDict(
                name=validator_name,
                ok=False,
                finding_validator_status=[],
                examination_validator_status=[],
                issues=[
                    _build_issue(
                        code="unknown_examination_validator_reference",
                        message=(
                            f"Examination validator '{validator_name}' is referenced but "
                            "is not defined."
                        ),
                        validator_name=validator_name,
                        validator_kind="examination_validator",
                    )
                ],
            )
            exam_cache[validator_name] = result
            return result

        stack.append(validator_name)
        findings_status: List[ExaminationValidatorDependencyStatusDataDict] = []
        exams_status: List[ExaminationValidatorDependencyStatusDataDict] = []
        issues: List[RuntimeValidationIssueDataDict] = []
        ok = True

        for dep_name in _as_str_list(validator.finding_validators):
            dep_result = evaluate_finding_validator_by_name(dep_name)
            findings_status.append(
                ExaminationValidatorDependencyStatusDataDict(
                    name=dep_name, ok=dep_result["ok"]
                )
            )
            if dep_result["ok"]:
                continue
            ok = False
            issues.append(
                _build_issue(
                    code="failed_finding_validator_dependency",
                    message=(
                        f"Examination validator '{validator_name}' depends on failing "
                        f"findings validator '{dep_name}'."
                    ),
                    validator_name=validator_name,
                    validator_kind="examination_validator",
                    details={"dependency": dep_name},
                )
            )
            issues.extend(dep_result["issues"])

        for dep_name in _as_str_list(validator.examination_validators):
            dep_result = evaluate_examination_validator_by_name(dep_name, stack)
            exams_status.append(
                ExaminationValidatorDependencyStatusDataDict(
                    name=dep_name, ok=dep_result["ok"]
                )
            )
            if dep_result["ok"]:
                continue
            ok = False
            issues.append(
                _build_issue(
                    code="failed_examination_validator_dependency",
                    message=(
                        f"Examination validator '{validator_name}' depends on failing "
                        f"examination validator '{dep_name}'."
                    ),
                    validator_name=validator_name,
                    validator_kind="examination_validator",
                    details={"dependency": dep_name},
                )
            )
            issues.extend(dep_result["issues"])

        stack.pop()
        result = ExaminationValidatorExecutionDataDict(
            name=validator_name,
            ok=ok,
            finding_validator_status=findings_status,
            examination_validator_status=exams_status,
            issues=issues,
        )
        exam_cache[validator_name] = result
        return result

    findings_results = [
        evaluate_finding_validator_by_name(name)
        for name in _as_str_list(template.validators.findings_validators)
    ]
    exam_results = [
        evaluate_examination_validator_by_name(name, [])
        for name in _as_str_list(template.validators.examination_validators)
    ]

    issues: List[RuntimeValidationIssueDataDict] = []
    for result in findings_results:
        issues.extend(result["issues"])
    for result in exam_results:
        issues.extend(result["issues"])

    ok = all(result["ok"] for result in findings_results) and all(
        result["ok"] for result in exam_results
    )

    return ReportTemplateRuntimeValidationResultDataDict(
        template_name=template.name,
        ok=ok,
        evaluated_findings_count=len(normalized_findings),
        findings_validators=findings_results,
        examination_validators=exam_results,
        issues=issues,
    )


__all__ = [
    "RuntimeValidationIssueDataDict",
    "ExaminationValidatorDependencyStatusDataDict",
    "FindingsValidatorExecutionDataDict",
    "ExaminationValidatorExecutionDataDict",
    "ReportTemplateRuntimeValidationResultDataDict",
    "evaluate_findings_validator_runtime",
    "evaluate_report_template_validators_runtime",
]
