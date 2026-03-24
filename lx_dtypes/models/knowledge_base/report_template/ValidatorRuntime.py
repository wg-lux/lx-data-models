from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Literal, Mapping, Sequence, TypedDict

from ..classification.Classification import Classification
from ..classification_choice.ClassificationChoice import ClassificationChoice
from ..classification_choice_descriptor.ClassificationChoiceDescriptor import (
    ClassificationChoiceDescriptor,
)
from ..intervention.Intervention import Intervention
from ..unit.Unit import Unit
from .ClassificationValidator import (
    ClassificationValidator,
    ClassificationValidatorCondition,
)
from .ClassificationValidatorDataDict import ClassificationValidatorHintDataDict
from .InterventionValidator import (
    InterventionValidator,
    InterventionValidatorCondition,
)
from .InterventionValidatorDataDict import InterventionValidatorHintDataDict
from .ExaminationValidator import ExaminationValidator
from .FindingsValidator import (
    FindingsValidator,
    FindingsValidatorCondition,
    FindingsValidatorConditionClause,
)
from .ReportTemplate import ReportTemplate
from .UnitValidator import UnitValidator, UnitValidatorCondition
from .UnitValidatorDataDict import UnitValidatorHintDataDict
from .ValidatorRequirementReference import ValidatorRequirementReference
from .ValueTypes import (
    ValidationIssueDetails,
    ValidationScalar,
    ValidationValue,
)


class RuntimeValidationIssueDataDict(TypedDict, total=False):
    code: str
    level: Literal["error", "warning"]
    message: str
    validator_name: str
    validator_kind: Literal[
        "classification_validator",
        "intervention_validator",
        "findings_validator",
        "examination_validator",
        "template",
        "unit_validator",
    ]
    details: ValidationIssueDetails


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


class ClassificationValidatorExecutionDataDict(TypedDict):
    name: str
    ok: bool
    operator: str
    finding: str
    classification: str
    precedence: Literal["required", "optional"]
    matched_occurrences: int
    triggered_occurrences: int
    hint: ClassificationValidatorHintDataDict
    issues: List[RuntimeValidationIssueDataDict]


class InterventionValidatorExecutionDataDict(TypedDict):
    name: str
    ok: bool
    operator: str
    finding: str
    intervention: str
    precedence: Literal["required", "optional"]
    matched_occurrences: int
    triggered_occurrences: int
    hint: InterventionValidatorHintDataDict
    issues: List[RuntimeValidationIssueDataDict]


class UnitValidatorExecutionDataDict(TypedDict):
    name: str
    ok: bool
    operator: str
    finding: str
    classification: str
    unit: str
    precedence: Literal["required", "optional"]
    matched_occurrences: int
    triggered_occurrences: int
    hint: UnitValidatorHintDataDict
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
    classification_validators: List[ClassificationValidatorExecutionDataDict]
    intervention_validators: List[InterventionValidatorExecutionDataDict]
    findings_validators: List[FindingsValidatorExecutionDataDict]
    examination_validators: List[ExaminationValidatorExecutionDataDict]
    unit_validators: List[UnitValidatorExecutionDataDict]
    issues: List[RuntimeValidationIssueDataDict]


class _RuntimeFindingOccurrence(TypedDict):
    finding: str
    classifications: Dict[str, List[ValidationScalar]]
    classification_units: Dict[str, List[str]]
    interventions: List[str]


@dataclass(frozen=True)
class _NormalizedConditionClause:
    classification: str
    comparator: str
    expected_values: tuple[ValidationScalar, ...]


@dataclass(frozen=True)
class _NormalizedCondition:
    any_clauses: tuple[_NormalizedConditionClause, ...]
    all_clauses: tuple[_NormalizedConditionClause, ...]


def _as_str_list(value: object) -> List[str]:
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


def _normalize_identifier(value: object) -> str:
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


def _coerce_validation_scalar(value: object) -> ValidationScalar | None:
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        token = _normalize_identifier(value)
        return token or None
    return str(value)


def _coerce_validation_value(value: object) -> ValidationValue | None:
    if isinstance(value, list):
        result: list[ValidationScalar] = []
        for item in value:
            coerced = _coerce_validation_scalar(item)
            if coerced is not None:
                result.append(coerced)
        return result
    return _coerce_validation_scalar(value)


def _extract_classification_value(
    payload: Mapping[str, object],
) -> ValidationValue | None:
    for key in ("value", "classification_choice", "classificationChoice", "choice"):
        if key in payload:
            return _coerce_validation_value(payload.get(key))
    if "values" in payload:
        values = payload.get("values")
        if isinstance(values, list):
            return _coerce_validation_value(values)
    return None


def _extract_classification_unit(payload: Mapping[str, object]) -> str | None:
    for key in ("unit", "unit_name", "classification_unit"):
        if key in payload:
            unit_name = _normalize_identifier(payload.get(key))
            if unit_name:
                return unit_name
    return None


def _add_classification_value(
    target: Dict[str, List[ValidationScalar]],
    classification_name: object,
    value: ValidationValue | None,
) -> None:
    normalized_name = _normalize_identifier(classification_name)
    if not normalized_name:
        return

    bucket = target.setdefault(normalized_name, [])
    if isinstance(value, list):
        for item in value:
            bucket.append(item)
        return
    if value is not None:
        bucket.append(value)
        return
    # If no explicit value exists, still mark the classification as present.
    bucket.append(True)


def _add_classification_unit(
    target: Dict[str, List[str]], classification_name: object, unit_name: object
) -> None:
    normalized_name = _normalize_identifier(classification_name)
    normalized_unit = _normalize_identifier(unit_name)
    if not normalized_name or not normalized_unit:
        return
    bucket = target.setdefault(normalized_name, [])
    bucket.append(normalized_unit)


def _normalize_interventions(raw: object) -> List[str]:
    if raw is None:
        return []
    if isinstance(raw, Mapping):
        token = _normalize_identifier(raw.get("intervention"))
        if token:
            return [token]
        token = _normalize_identifier(raw.get("name"))
        return [token] if token else []
    if not isinstance(raw, list):
        token = _normalize_identifier(raw)
        return [token] if token else []

    interventions: List[str] = []
    for item in raw:
        if isinstance(item, Mapping):
            token = _normalize_identifier(item.get("intervention"))
            if not token:
                token = _normalize_identifier(item.get("name"))
        else:
            token = _normalize_identifier(item)
        if token:
            interventions.append(token)
    return interventions


def _normalize_classifications(
    raw: object,
) -> tuple[Dict[str, List[ValidationScalar]], Dict[str, List[str]]]:
    normalized: Dict[str, List[ValidationScalar]] = {}
    units: Dict[str, List[str]] = {}
    if raw is None:
        return normalized, units

    if isinstance(raw, Mapping):
        for class_name, class_value in raw.items():
            _add_classification_value(normalized, class_name, class_value)
        return normalized, units

    if not isinstance(raw, list):
        return normalized, units

    for item in raw:
        if isinstance(item, Mapping):
            classification_name = item.get("classification")
            if classification_name is None:
                classification_name = item.get("name")
            if classification_name is None:
                classification_name = item.get("key")
            class_value = _extract_classification_value(item)
            _add_classification_value(normalized, classification_name, class_value)
            _add_classification_unit(
                units, classification_name, _extract_classification_unit(item)
            )
            continue

        _add_classification_value(normalized, item, True)

    return normalized, units


def _normalize_reported_findings(
    reported_findings: Sequence[Mapping[str, object]] | None,
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

        classifications, classification_units = _normalize_classifications(
            finding_payload.get("classifications")
        )
        occurrences.append(
            _RuntimeFindingOccurrence(
                finding=finding_name,
                classifications=classifications,
                classification_units=classification_units,
                interventions=_normalize_interventions(
                    finding_payload.get("interventions")
                ),
            )
        )

    return occurrences


def _coerce_numeric(value: ValidationScalar) -> float | None:
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


def _value_equals(left: ValidationScalar, right: ValidationScalar) -> bool:
    if left == right:
        return True

    left_num = _coerce_numeric(left)
    right_num = _coerce_numeric(right)
    if left_num is not None and right_num is not None:
        return left_num == right_num

    return str(left) == str(right)


def _compare_ordered(
    left: ValidationScalar, right: ValidationScalar, operator: str
) -> bool:
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


def _normalize_condition_clause(
    clause: FindingsValidatorConditionClause,
) -> _NormalizedConditionClause | None:
    expected_values = tuple(clause.values or ())
    if clause.value is not None and not expected_values:
        expected_values = (clause.value,)
    if not clause.classification or not expected_values:
        return None
    return _NormalizedConditionClause(
        classification=clause.classification,
        comparator=clause.comparator,
        expected_values=expected_values,
    )


def _normalize_condition(
    condition: (
        FindingsValidatorCondition
        | ClassificationValidatorCondition
        | InterventionValidatorCondition
        | UnitValidatorCondition
    ),
) -> _NormalizedCondition:
    any_clauses = tuple(
        normalized
        for clause in condition.any or []
        for normalized in [_normalize_condition_clause(clause)]
        if normalized is not None
    )
    all_clauses = tuple(
        normalized
        for clause in condition.all or []
        for normalized in [_normalize_condition_clause(clause)]
        if normalized is not None
    )
    return _NormalizedCondition(
        any_clauses=any_clauses,
        all_clauses=all_clauses,
    )


def _evaluate_clause(
    clause: _NormalizedConditionClause,
    classifications: Mapping[str, List[ValidationScalar]],
) -> bool:
    actual_values = classifications.get(clause.classification, [])
    if not actual_values:
        return False

    comparator = clause.comparator
    primary_expected_value = clause.expected_values[0]
    if comparator == "eq":
        return any(
            _value_equals(value, primary_expected_value) for value in actual_values
        )
    if comparator == "ne":
        return all(
            not _value_equals(value, primary_expected_value) for value in actual_values
        )
    if comparator in {"gt", "gte", "lt", "lte"}:
        return any(
            _compare_ordered(value, primary_expected_value, comparator)
            for value in actual_values
        )

    expected_values = clause.expected_values

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
    condition: FindingsValidatorCondition,
    classifications: Mapping[str, List[ValidationScalar]],
) -> bool:
    normalized_condition = _normalize_condition(condition)
    any_clauses = normalized_condition.any_clauses
    all_clauses = normalized_condition.all_clauses

    any_match = True
    if any_clauses:
        any_match = any(
            _evaluate_clause(clause, classifications) for clause in any_clauses
        )

    all_match = True
    if all_clauses:
        all_match = all(
            _evaluate_clause(clause, classifications) for clause in all_clauses
        )

    return any_match and all_match


def _classification_condition_matches(
    condition: (
        ClassificationValidatorCondition
        | InterventionValidatorCondition
        | UnitValidatorCondition
    ),
    classifications: Mapping[str, List[ValidationScalar]],
) -> bool:
    normalized_condition = _normalize_condition(condition)
    any_clauses = normalized_condition.any_clauses
    all_clauses = normalized_condition.all_clauses

    any_match = True
    if any_clauses:
        any_match = any(
            _evaluate_clause(clause, classifications) for clause in any_clauses
        )

    all_match = True
    if all_clauses:
        all_match = all(
            _evaluate_clause(clause, classifications) for clause in all_clauses
        )

    return any_match and all_match


def _missing_required_classifications(
    condition: FindingsValidatorCondition,
    classifications: Mapping[str, List[ValidationScalar]],
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


def _missing_requirement_references(
    requirements: Sequence[ValidatorRequirementReference],
    *,
    occurrence: _RuntimeFindingOccurrence,
    all_occurrences: Sequence[_RuntimeFindingOccurrence],
) -> List[str]:
    missing: List[str] = []
    for requirement in requirements:
        if requirement.kind == "classification":
            if occurrence["classifications"].get(requirement.name):
                continue
            missing.append(f"classification:{requirement.name}")
            continue
        if requirement.kind == "finding":
            if any(item["finding"] == requirement.name for item in all_occurrences):
                continue
            missing.append(f"finding:{requirement.name}")
            continue
        if requirement.kind == "intervention":
            if requirement.name in occurrence["interventions"]:
                continue
            missing.append(f"intervention:{requirement.name}")
            continue
        if requirement.kind == "unit":
            units = occurrence["classification_units"].get(
                requirement.classification or "", []
            )
            if requirement.name in units:
                continue
            missing.append(f"unit:{requirement.name}")
    return missing


def _build_issue(
    *,
    code: str,
    message: str,
    validator_name: str,
    validator_kind: Literal[
        "classification_validator",
        "findings_validator",
        "examination_validator",
        "intervention_validator",
        "unit_validator",
        "template",
    ],
    level: Literal["error", "warning"] = "error",
    details: ValidationIssueDetails | None = None,
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


def _classification_data_type_hint(
    *,
    classification: Classification | None,
    classification_choices: Mapping[str, ClassificationChoice],
    classification_choice_descriptors: Mapping[str, ClassificationChoiceDescriptor],
) -> tuple[
    Literal["binary", "non_categorical", "ordered", "unknown"],
    List[str],
    List[str],
    bool,
]:
    if classification is None:
        return "unknown", [], [], False

    choice_names = _as_str_list(classification.classification_choices)
    descriptor_types: set[str] = set()
    allows_multiple = False

    for choice_name in choice_names:
        choice = classification_choices.get(choice_name)
        if choice is None:
            continue
        descriptor_names = _as_str_list(choice.classification_choice_descriptors)
        for descriptor_name in descriptor_names:
            descriptor = classification_choice_descriptors.get(descriptor_name)
            if descriptor is None:
                continue
            descriptor_type = _normalize_identifier(
                descriptor.classification_choice_descriptor_type
            )
            if descriptor_type:
                descriptor_types.add(descriptor_type)
            allows_multiple = allows_multiple or bool(descriptor.selection_multiple)

    if "boolean" in descriptor_types or len(choice_names) == 2:
        return "binary", choice_names, sorted(descriptor_types), allows_multiple
    if descriptor_types.intersection({"numeric", "text"}):
        return (
            "non_categorical",
            choice_names,
            sorted(descriptor_types),
            allows_multiple,
        )
    if choice_names:
        return "ordered", choice_names, sorted(descriptor_types), allows_multiple
    return "non_categorical", choice_names, sorted(descriptor_types), allows_multiple


def _build_classification_hint(
    *,
    validator: ClassificationValidator,
    classifications: Mapping[str, Classification],
    classification_choices: Mapping[str, ClassificationChoice],
    classification_choice_descriptors: Mapping[str, ClassificationChoiceDescriptor],
) -> ClassificationValidatorHintDataDict:
    classification = classifications.get(validator.classification)
    (
        data_type_hint,
        choice_names,
        descriptor_types,
        allows_multiple,
    ) = _classification_data_type_hint(
        classification=classification,
        classification_choices=classification_choices,
        classification_choice_descriptors=classification_choice_descriptors,
    )

    hint = ClassificationValidatorHintDataDict(
        classification_name=validator.classification,
        precedence=validator.precedence,
        data_type_hint=data_type_hint,
    )
    if choice_names:
        hint["choice_names"] = choice_names
    if descriptor_types:
        hint["descriptor_types"] = descriptor_types
    if allows_multiple:
        hint["allows_multiple"] = True
    return hint


def _build_intervention_hint(
    *,
    validator: InterventionValidator,
    interventions: Mapping[str, Intervention],
) -> InterventionValidatorHintDataDict:
    intervention = interventions.get(validator.intervention)
    hint = InterventionValidatorHintDataDict(
        intervention_name=validator.intervention,
        precedence=validator.precedence,
    )
    if intervention is not None:
        intervention_types = _as_str_list(intervention.intervention_types)
        if intervention_types:
            hint["intervention_types"] = intervention_types
    return hint


def _build_unit_hint(
    *,
    validator: UnitValidator,
    units: Mapping[str, Unit],
) -> UnitValidatorHintDataDict:
    unit = units.get(validator.unit)
    hint = UnitValidatorHintDataDict(
        unit_name=validator.unit,
        precedence=validator.precedence,
    )
    if unit is not None:
        if unit.abbreviation:
            hint["abbreviation"] = unit.abbreviation
        unit_types = _as_str_list(unit.unit_types)
        if unit_types:
            hint["unit_types"] = unit_types
    return hint


def evaluate_findings_validator_runtime(
    validator: FindingsValidator,
    *,
    reported_findings: Sequence[Mapping[str, object]] | None = None,
) -> FindingsValidatorExecutionDataDict:
    normalized_findings = _normalize_reported_findings(reported_findings)
    target_finding = validator.finding
    matched_occurrences = [
        finding
        for finding in normalized_findings
        if finding["finding"] == target_finding
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
    elif validator.operator == "condition":
        condition = validator.query.condition
        if condition is None:
            ok = False
            issues.append(
                _build_issue(
                    code="invalid_conditional_validator_definition",
                    message=(
                        f"Validator '{validator.name}' uses 'condition' operator but "
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
                missing_generic = _missing_requirement_references(
                    condition.then_requires,
                    occurrence=occurrence,
                    all_occurrences=normalized_findings,
                )
                if not missing:
                    if not missing_generic:
                        continue
                missing.extend(
                    [
                        token.split(":", 1)[1]
                        for token in missing_generic
                        if token.startswith("classification:")
                    ]
                )
                missing_required_classifications.extend(missing)
                issues.append(
                    _build_issue(
                        code=(
                            "missing_required_classification"
                            if missing
                            else "missing_required_reference"
                        ),
                        message=(
                            f"Validator '{validator.name}' requires "
                            f"{', '.join(missing or missing_generic)} when condition is met."
                        ),
                        validator_name=validator.name,
                        validator_kind="findings_validator",
                        details={
                            "occurrence_index": occurrence_index,
                            "missing_classifications": missing,
                            "missing_requirements": missing_generic,
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


def evaluate_classification_validator_runtime(
    validator: ClassificationValidator,
    *,
    classifications: Mapping[str, Classification],
    classification_choices: Mapping[str, ClassificationChoice],
    classification_choice_descriptors: Mapping[str, ClassificationChoiceDescriptor],
    reported_findings: Sequence[Mapping[str, object]] | None = None,
) -> ClassificationValidatorExecutionDataDict:
    normalized_findings = _normalize_reported_findings(reported_findings)
    target_finding = validator.finding
    target_classification = validator.classification
    matched_occurrences = [
        finding
        for finding in normalized_findings
        if finding["finding"] == target_finding
    ]

    issues: List[RuntimeValidationIssueDataDict] = []
    triggered_occurrences = 0
    hint = _build_classification_hint(
        validator=validator,
        classifications=classifications,
        classification_choices=classification_choices,
        classification_choice_descriptors=classification_choice_descriptors,
    )

    if validator.operator == "exists":
        if not matched_occurrences:
            ok = False
            issues.append(
                _build_issue(
                    code="finding_not_present_for_classification_validator",
                    message=(
                        f"Finding '{target_finding}' is not present for classification "
                        f"validator '{validator.name}'."
                    ),
                    validator_name=validator.name,
                    validator_kind="classification_validator",
                )
            )
        else:
            ok = any(
                occurrence["classifications"].get(target_classification)
                for occurrence in matched_occurrences
            )
            if not ok:
                issues.append(
                    _build_issue(
                        code="classification_not_present",
                        message=(
                            f"Classification '{target_classification}' is required by "
                            f"validator '{validator.name}' but is not present."
                        ),
                        validator_name=validator.name,
                        validator_kind="classification_validator",
                    )
                )
    elif validator.operator == "missing":
        ok = all(
            not occurrence["classifications"].get(target_classification)
            for occurrence in matched_occurrences
        )
        if not ok:
            issues.append(
                _build_issue(
                    code="classification_present_but_should_be_missing",
                    message=(
                        f"Classification '{target_classification}' should be absent "
                        f"for validator '{validator.name}'."
                    ),
                    validator_name=validator.name,
                    validator_kind="classification_validator",
                )
            )
    elif validator.operator == "condition":
        condition = validator.query.condition
        if condition is None:
            ok = False
            issues.append(
                _build_issue(
                    code="invalid_conditional_classification_validator_definition",
                    message=(
                        f"Validator '{validator.name}' uses 'condition' operator but "
                        "has no condition block."
                    ),
                    validator_name=validator.name,
                    validator_kind="classification_validator",
                )
            )
        else:
            if not matched_occurrences:
                ok = False
                issues.append(
                    _build_issue(
                        code="finding_not_present_for_classification_validator",
                        message=(
                            f"Finding '{target_finding}' is not present for classification "
                            f"validator '{validator.name}'."
                        ),
                        validator_name=validator.name,
                        validator_kind="classification_validator",
                    )
                )
            else:
                ok = True
                for occurrence_index, occurrence in enumerate(matched_occurrences):
                    if not _classification_condition_matches(
                        condition, occurrence["classifications"]
                    ):
                        continue
                    triggered_occurrences += 1
                    missing_requirements = _missing_requirement_references(
                        condition.then_requires,
                        occurrence=occurrence,
                        all_occurrences=normalized_findings,
                    )
                    if (
                        occurrence["classifications"].get(target_classification)
                        and not missing_requirements
                    ):
                        continue
                    ok = False
                    issues.append(
                        _build_issue(
                            code=(
                                "missing_required_classification"
                                if not missing_requirements
                                else "missing_required_reference"
                            ),
                            message=(
                                f"Validator '{validator.name}' requires classification "
                                f"'{target_classification}'"
                                + (
                                    f" and {', '.join(missing_requirements)}"
                                    if missing_requirements
                                    else ""
                                )
                                + " when condition is met."
                            ),
                            validator_name=validator.name,
                            validator_kind="classification_validator",
                            details={
                                "occurrence_index": occurrence_index,
                                "missing_classification": target_classification,
                                "missing_requirements": missing_requirements,
                            },
                        )
                    )
    else:
        ok = False
        issues.append(
            _build_issue(
                code="unsupported_classification_validator_operator",
                message=(
                    f"Operator '{validator.operator}' is not supported by the runtime "
                    "validator engine."
                ),
                validator_name=validator.name,
                validator_kind="classification_validator",
            )
        )

    return ClassificationValidatorExecutionDataDict(
        name=validator.name,
        ok=ok,
        operator=validator.operator,
        finding=target_finding,
        classification=target_classification,
        precedence=validator.precedence,
        matched_occurrences=len(matched_occurrences),
        triggered_occurrences=triggered_occurrences,
        hint=hint,
        issues=issues,
    )


def evaluate_intervention_validator_runtime(
    validator: InterventionValidator,
    *,
    interventions: Mapping[str, Intervention],
    reported_findings: Sequence[Mapping[str, object]] | None = None,
) -> InterventionValidatorExecutionDataDict:
    normalized_findings = _normalize_reported_findings(reported_findings)
    matched_occurrences = [
        finding
        for finding in normalized_findings
        if finding["finding"] == validator.finding
    ]
    issues: List[RuntimeValidationIssueDataDict] = []
    triggered_occurrences = 0
    hint = _build_intervention_hint(validator=validator, interventions=interventions)

    if validator.operator == "exists":
        ok = any(
            validator.intervention in occurrence["interventions"]
            for occurrence in matched_occurrences
        )
        if not ok:
            issues.append(
                _build_issue(
                    code="intervention_not_present",
                    message=(
                        f"Intervention '{validator.intervention}' is required by "
                        f"validator '{validator.name}' but is not present."
                    ),
                    validator_name=validator.name,
                    validator_kind="intervention_validator",
                )
            )
    elif validator.operator == "missing":
        ok = all(
            validator.intervention not in occurrence["interventions"]
            for occurrence in matched_occurrences
        )
        if not ok:
            issues.append(
                _build_issue(
                    code="intervention_present_but_should_be_missing",
                    message=(
                        f"Intervention '{validator.intervention}' should be absent "
                        f"for validator '{validator.name}'."
                    ),
                    validator_name=validator.name,
                    validator_kind="intervention_validator",
                )
            )
    elif validator.operator == "condition":
        condition = validator.query.condition
        ok = True
        if condition is None:
            ok = False
            issues.append(
                _build_issue(
                    code="invalid_conditional_intervention_validator_definition",
                    message=(
                        f"Validator '{validator.name}' uses 'condition' operator but "
                        "has no condition block."
                    ),
                    validator_name=validator.name,
                    validator_kind="intervention_validator",
                )
            )
        else:
            for occurrence_index, occurrence in enumerate(matched_occurrences):
                if not _classification_condition_matches(
                    condition, occurrence["classifications"]
                ):
                    continue
                triggered_occurrences += 1
                missing_requirements = _missing_requirement_references(
                    condition.then_requires,
                    occurrence=occurrence,
                    all_occurrences=normalized_findings,
                )
                if (
                    validator.intervention in occurrence["interventions"]
                    and not missing_requirements
                ):
                    continue
                ok = False
                issues.append(
                    _build_issue(
                        code="missing_required_intervention",
                        message=(
                            f"Validator '{validator.name}' requires intervention "
                            f"'{validator.intervention}' when condition is met."
                        ),
                        validator_name=validator.name,
                        validator_kind="intervention_validator",
                        details={
                            "occurrence_index": occurrence_index,
                            "missing_requirements": missing_requirements,
                        },
                    )
                )
    else:
        ok = False
        issues.append(
            _build_issue(
                code="unsupported_intervention_validator_operator",
                message=(
                    f"Operator '{validator.operator}' is not supported by the runtime "
                    "validator engine."
                ),
                validator_name=validator.name,
                validator_kind="intervention_validator",
            )
        )

    return InterventionValidatorExecutionDataDict(
        name=validator.name,
        ok=ok,
        operator=validator.operator,
        finding=validator.finding,
        intervention=validator.intervention,
        precedence=validator.precedence,
        matched_occurrences=len(matched_occurrences),
        triggered_occurrences=triggered_occurrences,
        hint=hint,
        issues=issues,
    )


def evaluate_unit_validator_runtime(
    validator: UnitValidator,
    *,
    units: Mapping[str, Unit],
    reported_findings: Sequence[Mapping[str, object]] | None = None,
) -> UnitValidatorExecutionDataDict:
    normalized_findings = _normalize_reported_findings(reported_findings)
    matched_occurrences = [
        finding
        for finding in normalized_findings
        if finding["finding"] == validator.finding
    ]
    issues: List[RuntimeValidationIssueDataDict] = []
    triggered_occurrences = 0
    hint = _build_unit_hint(validator=validator, units=units)

    def occurrence_has_unit(occurrence: _RuntimeFindingOccurrence) -> bool:
        return validator.unit in occurrence["classification_units"].get(
            validator.classification, []
        )

    if validator.operator == "exists":
        ok = any(occurrence_has_unit(occurrence) for occurrence in matched_occurrences)
        if not ok:
            issues.append(
                _build_issue(
                    code="unit_not_present",
                    message=(
                        f"Unit '{validator.unit}' is required by validator "
                        f"'{validator.name}' but is not present."
                    ),
                    validator_name=validator.name,
                    validator_kind="unit_validator",
                )
            )
    elif validator.operator == "missing":
        ok = all(
            not occurrence_has_unit(occurrence) for occurrence in matched_occurrences
        )
        if not ok:
            issues.append(
                _build_issue(
                    code="unit_present_but_should_be_missing",
                    message=(
                        f"Unit '{validator.unit}' should be absent for validator "
                        f"'{validator.name}'."
                    ),
                    validator_name=validator.name,
                    validator_kind="unit_validator",
                )
            )
    elif validator.operator == "condition":
        condition = validator.query.condition
        ok = True
        if condition is None:
            ok = False
            issues.append(
                _build_issue(
                    code="invalid_conditional_unit_validator_definition",
                    message=(
                        f"Validator '{validator.name}' uses 'condition' operator but "
                        "has no condition block."
                    ),
                    validator_name=validator.name,
                    validator_kind="unit_validator",
                )
            )
        else:
            for occurrence_index, occurrence in enumerate(matched_occurrences):
                if not _classification_condition_matches(
                    condition, occurrence["classifications"]
                ):
                    continue
                triggered_occurrences += 1
                missing_requirements = _missing_requirement_references(
                    condition.then_requires,
                    occurrence=occurrence,
                    all_occurrences=normalized_findings,
                )
                if occurrence_has_unit(occurrence) and not missing_requirements:
                    continue
                ok = False
                issues.append(
                    _build_issue(
                        code="missing_required_unit",
                        message=(
                            f"Validator '{validator.name}' requires unit "
                            f"'{validator.unit}' when condition is met."
                        ),
                        validator_name=validator.name,
                        validator_kind="unit_validator",
                        details={
                            "occurrence_index": occurrence_index,
                            "missing_requirements": missing_requirements,
                        },
                    )
                )
    else:
        ok = False
        issues.append(
            _build_issue(
                code="unsupported_unit_validator_operator",
                message=(
                    f"Operator '{validator.operator}' is not supported by the runtime "
                    "validator engine."
                ),
                validator_name=validator.name,
                validator_kind="unit_validator",
            )
        )

    return UnitValidatorExecutionDataDict(
        name=validator.name,
        ok=ok,
        operator=validator.operator,
        finding=validator.finding,
        classification=validator.classification,
        unit=validator.unit,
        precedence=validator.precedence,
        matched_occurrences=len(matched_occurrences),
        triggered_occurrences=triggered_occurrences,
        hint=hint,
        issues=issues,
    )


def evaluate_report_template_validators_runtime(
    template: ReportTemplate,
    *,
    classification_validators: Mapping[str, ClassificationValidator],
    classification_validator_names: Sequence[str] | None = None,
    intervention_validators: Mapping[str, InterventionValidator],
    unit_validators: Mapping[str, UnitValidator],
    findings_validators: Mapping[str, FindingsValidator],
    examination_validators: Mapping[str, ExaminationValidator],
    classifications: Mapping[str, Classification],
    classification_choices: Mapping[str, ClassificationChoice],
    classification_choice_descriptors: Mapping[str, ClassificationChoiceDescriptor],
    interventions: Mapping[str, Intervention],
    units: Mapping[str, Unit],
    reported_findings: Sequence[Mapping[str, object]] | None = None,
) -> ReportTemplateRuntimeValidationResultDataDict:
    normalized_findings = _normalize_reported_findings(reported_findings)

    classification_cache: Dict[str, ClassificationValidatorExecutionDataDict] = {}
    intervention_cache: Dict[str, InterventionValidatorExecutionDataDict] = {}
    findings_cache: Dict[str, FindingsValidatorExecutionDataDict] = {}
    exam_cache: Dict[str, ExaminationValidatorExecutionDataDict] = {}
    unit_cache: Dict[str, UnitValidatorExecutionDataDict] = {}

    def evaluate_classification_validator_by_name(
        validator_name: str,
    ) -> ClassificationValidatorExecutionDataDict:
        cached = classification_cache.get(validator_name)
        if cached is not None:
            return cached

        validator = classification_validators.get(validator_name)
        if validator is None:
            result = ClassificationValidatorExecutionDataDict(
                name=validator_name,
                ok=False,
                operator="unknown",
                finding="unknown",
                classification="unknown",
                precedence="required",
                matched_occurrences=0,
                triggered_occurrences=0,
                hint=ClassificationValidatorHintDataDict(
                    classification_name="unknown",
                    precedence="required",
                    data_type_hint="unknown",
                ),
                issues=[
                    _build_issue(
                        code="unknown_classification_validator_reference",
                        message=(
                            f"Classification validator '{validator_name}' is referenced "
                            "but is not defined."
                        ),
                        validator_name=validator_name,
                        validator_kind="classification_validator",
                    )
                ],
            )
            classification_cache[validator_name] = result
            return result

        result = evaluate_classification_validator_runtime(
            validator,
            classifications=classifications,
            classification_choices=classification_choices,
            classification_choice_descriptors=classification_choice_descriptors,
            reported_findings=normalized_findings,
        )
        classification_cache[validator_name] = result
        return result

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

    def evaluate_intervention_validator_by_name(
        validator_name: str,
    ) -> InterventionValidatorExecutionDataDict:
        cached = intervention_cache.get(validator_name)
        if cached is not None:
            return cached

        validator = intervention_validators.get(validator_name)
        if validator is None:
            result = InterventionValidatorExecutionDataDict(
                name=validator_name,
                ok=False,
                operator="unknown",
                finding="unknown",
                intervention="unknown",
                precedence="required",
                matched_occurrences=0,
                triggered_occurrences=0,
                hint=InterventionValidatorHintDataDict(
                    intervention_name="unknown",
                    precedence="required",
                ),
                issues=[
                    _build_issue(
                        code="unknown_intervention_validator_reference",
                        message=(
                            f"Intervention validator '{validator_name}' is referenced "
                            "but is not defined."
                        ),
                        validator_name=validator_name,
                        validator_kind="intervention_validator",
                    )
                ],
            )
            intervention_cache[validator_name] = result
            return result

        result = evaluate_intervention_validator_runtime(
            validator,
            interventions=interventions,
            reported_findings=normalized_findings,
        )
        intervention_cache[validator_name] = result
        return result

    def evaluate_unit_validator_by_name(
        validator_name: str,
    ) -> UnitValidatorExecutionDataDict:
        cached = unit_cache.get(validator_name)
        if cached is not None:
            return cached

        validator = unit_validators.get(validator_name)
        if validator is None:
            result = UnitValidatorExecutionDataDict(
                name=validator_name,
                ok=False,
                operator="unknown",
                finding="unknown",
                classification="unknown",
                unit="unknown",
                precedence="required",
                matched_occurrences=0,
                triggered_occurrences=0,
                hint=UnitValidatorHintDataDict(
                    unit_name="unknown",
                    precedence="required",
                ),
                issues=[
                    _build_issue(
                        code="unknown_unit_validator_reference",
                        message=(
                            f"Unit validator '{validator_name}' is referenced but "
                            "is not defined."
                        ),
                        validator_name=validator_name,
                        validator_kind="unit_validator",
                    )
                ],
            )
            unit_cache[validator_name] = result
            return result

        result = evaluate_unit_validator_runtime(
            validator,
            units=units,
            reported_findings=normalized_findings,
        )
        unit_cache[validator_name] = result
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
            dep_finding_result = evaluate_finding_validator_by_name(dep_name)
            findings_status.append(
                ExaminationValidatorDependencyStatusDataDict(
                    name=dep_name, ok=dep_finding_result["ok"]
                )
            )
            if dep_finding_result["ok"]:
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
            issues.extend(dep_finding_result["issues"])

        for dep_name in _as_str_list(validator.examination_validators):
            dep_exam_result = evaluate_examination_validator_by_name(dep_name, stack)
            exams_status.append(
                ExaminationValidatorDependencyStatusDataDict(
                    name=dep_name, ok=dep_exam_result["ok"]
                )
            )
            if dep_exam_result["ok"]:
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
            issues.extend(dep_exam_result["issues"])

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
    intervention_results = [
        evaluate_intervention_validator_by_name(name)
        for name in _as_str_list(template.validators.intervention_validators)
    ]
    unit_results = [
        evaluate_unit_validator_by_name(name)
        for name in _as_str_list(template.validators.unit_validators)
    ]
    classification_results = [
        evaluate_classification_validator_by_name(name)
        for name in _as_str_list(
            classification_validator_names
            if classification_validator_names is not None
            else template.validators.classification_validators
        )
    ]
    exam_results = [
        evaluate_examination_validator_by_name(name, [])
        for name in _as_str_list(template.validators.examination_validators)
    ]

    issues: List[RuntimeValidationIssueDataDict] = []
    for classification_result in classification_results:
        issues.extend(classification_result["issues"])
    for intervention_result in intervention_results:
        issues.extend(intervention_result["issues"])
    for finding_result in findings_results:
        issues.extend(finding_result["issues"])
    for unit_result in unit_results:
        issues.extend(unit_result["issues"])
    for exam_result in exam_results:
        issues.extend(exam_result["issues"])

    ok = (
        all(result["ok"] for result in classification_results)
        and all(result["ok"] for result in intervention_results)
        and all(result["ok"] for result in findings_results)
        and all(result["ok"] for result in exam_results)
        and all(result["ok"] for result in unit_results)
    )

    return ReportTemplateRuntimeValidationResultDataDict(
        template_name=template.name,
        ok=ok,
        evaluated_findings_count=len(normalized_findings),
        classification_validators=classification_results,
        intervention_validators=intervention_results,
        findings_validators=findings_results,
        examination_validators=exam_results,
        unit_validators=unit_results,
        issues=issues,
    )


__all__ = [
    "RuntimeValidationIssueDataDict",
    "ClassificationValidatorExecutionDataDict",
    "InterventionValidatorExecutionDataDict",
    "ExaminationValidatorDependencyStatusDataDict",
    "FindingsValidatorExecutionDataDict",
    "ExaminationValidatorExecutionDataDict",
    "UnitValidatorExecutionDataDict",
    "ReportTemplateRuntimeValidationResultDataDict",
    "evaluate_classification_validator_runtime",
    "evaluate_findings_validator_runtime",
    "evaluate_intervention_validator_runtime",
    "evaluate_report_template_validators_runtime",
    "evaluate_unit_validator_runtime",
]
