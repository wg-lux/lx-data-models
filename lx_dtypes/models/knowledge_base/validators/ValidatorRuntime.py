"""Execute report-template validators and their condition dependencies."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Literal

from lx_dtypes.language import DEFAULT_LANGUAGE
from lx_dtypes.language import (
    validate_language as _validate_language,
)
from lx_dtypes.models.knowledge_base.report_template.ReportedFindings import (
    _as_str_list,
    _normalize_identifier,
    _normalize_reported_findings,
    _RuntimeFindingOccurrence,
)
from lx_dtypes.models.knowledge_base.report_template.ReportTemplate import (
    ReportTemplate,
)
from lx_dtypes.models.knowledge_base.validators.ClassificationValidator import (
    ClassificationValidator,
    ClassificationValidatorCondition,
)
from lx_dtypes.models.knowledge_base.validators.ClassificationValidatorDataDict import (
    ClassificationValidatorHintDataDict,
)
from lx_dtypes.models.knowledge_base.validators.ExaminationValidator import (
    ExaminationValidator,
)
from lx_dtypes.models.knowledge_base.validators.FindingsValidator import (
    FindingsValidator,
    FindingsValidatorCondition,
    FindingsValidatorConditionClause,
)
from lx_dtypes.models.knowledge_base.validators.InterventionValidator import (
    InterventionValidator,
    InterventionValidatorCondition,
)
from lx_dtypes.models.knowledge_base.validators.InterventionValidatorDataDict import (
    InterventionValidatorHintDataDict,
)
from lx_dtypes.models.knowledge_base.validators.RuntimeIssues import (
    RuntimeValidationLanguage,
    _build_issue,
    _runtime_message,
)
from lx_dtypes.models.knowledge_base.validators.UnitValidator import (
    UnitValidator,
    UnitValidatorCondition,
)
from lx_dtypes.models.knowledge_base.validators.UnitValidatorDataDict import (
    UnitValidatorHintDataDict,
)
from lx_dtypes.models.knowledge_base.validators.ValidatorRequirementReference import (
    ValidatorRequirementReference,
)
from lx_dtypes.models.knowledge_base.validators.ValidatorRuntimeDataDict import (
    ClassificationValidatorExecutionDataDict,
    ExaminationValidatorDependencyStatusDataDict,
    ExaminationValidatorExecutionDataDict,
    FindingsValidatorExecutionDataDict,
    InterventionValidatorExecutionDataDict,
    ReportTemplateRuntimeValidationResultDataDict,
    RuntimeValidationIssueDataDict,
    UnitValidatorExecutionDataDict,
)
from lx_dtypes.models.knowledge_base.validators.ValueTypes import (
    ValidationScalar,
)

from ..classification.Classification import Classification
from ..classification_choice.ClassificationChoice import ClassificationChoice
from ..classification_choice_descriptor.ClassificationChoiceDescriptor import (
    ClassificationChoiceDescriptor,
)
from ..intervention.Intervention import Intervention
from ..unit.Unit import Unit


@dataclass(frozen=True)
class _NormalizedConditionClause:
    classification: str
    comparator: str
    expected_values: tuple[ValidationScalar, ...]


@dataclass(frozen=True)
class _NormalizedCondition:
    any_clauses: tuple[_NormalizedConditionClause, ...]
    all_clauses: tuple[_NormalizedConditionClause, ...]


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
    expected_values = clause.expected_values
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
    classifications: Mapping[str, list[ValidationScalar]],
) -> bool | None:
    actual_values = classifications.get(clause.classification, [])
    if not actual_values:
        return None

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


def _condition_evaluation(
    condition: (
        FindingsValidatorCondition
        | ClassificationValidatorCondition
        | InterventionValidatorCondition
        | UnitValidatorCondition
    ),
    classifications: Mapping[str, list[ValidationScalar]],
) -> tuple[bool | None, list[str]]:
    normalized_condition = _normalize_condition(condition)
    any_clauses = normalized_condition.any_clauses
    all_clauses = normalized_condition.all_clauses
    missing: set[str] = set()

    any_match: bool | None = True
    if any_clauses:
        any_results = [
            (clause, _evaluate_clause(clause, classifications))
            for clause in any_clauses
        ]
        if any(result is True for _, result in any_results):
            any_match = True
        elif any(result is None for _, result in any_results):
            any_match = None
            missing.update(
                clause.classification
                for clause, result in any_results
                if result is None
            )
        else:
            any_match = False

    all_match: bool | None = True
    if all_clauses:
        all_results = [
            (clause, _evaluate_clause(clause, classifications))
            for clause in all_clauses
        ]
        if any(result is False for _, result in all_results):
            all_match = False
        elif any(result is None for _, result in all_results):
            all_match = None
            missing.update(
                clause.classification
                for clause, result in all_results
                if result is None
            )
        else:
            all_match = True

    if any_match is False or all_match is False:
        return False, []
    if any_match is None or all_match is None:
        return None, sorted(missing)
    return True, []


def _condition_matches(
    condition: FindingsValidatorCondition,
    classifications: Mapping[str, list[ValidationScalar]],
) -> bool:
    return _condition_evaluation(condition, classifications)[0] is True


def _classification_condition_matches(
    condition: (
        ClassificationValidatorCondition
        | InterventionValidatorCondition
        | UnitValidatorCondition
    ),
    classifications: Mapping[str, list[ValidationScalar]],
) -> bool:
    return _condition_evaluation(condition, classifications)[0] is True


def _missing_required_classifications(
    condition: FindingsValidatorCondition,
    classifications: Mapping[str, list[ValidationScalar]],
) -> list[str]:
    missing: list[str] = []
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
) -> list[str]:
    missing: list[str] = []
    for requirement in requirements:
        if requirement.kind == "classification":
            if occurrence["classifications"].get(requirement.name):
                continue
            missing.append(f"classification:{requirement.name}")
            continue
        if requirement.kind == "classification_choice":
            choice_names = list(dict.fromkeys([*requirement.names, requirement.name]))
            classifications = occurrence["classifications"]
            value_groups = (
                [classifications.get(requirement.classification, [])]
                if requirement.classification is not None
                else classifications.values()
            )
            reported_values = [
                str(value) for values in value_groups for value in values
            ]
            if any(choice_name in reported_values for choice_name in choice_names):
                continue
            missing.append(f"classification_choice:{'|'.join(choice_names)}")
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


def _classification_data_type_hint(
    *,
    classification: Classification | None,
    classification_choices: Mapping[str, ClassificationChoice],
    classification_choice_descriptors: Mapping[str, ClassificationChoiceDescriptor],
) -> tuple[
    Literal["binary", "non_categorical", "ordered", "unknown"],
    list[str],
    list[str],
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


def _classification_has_evaluable_value(
    values: Sequence[ValidationScalar],
    hint: ClassificationValidatorHintDataDict,
) -> bool:
    """Require a descriptor value when the KB declares descriptor-backed input."""

    descriptor_types = set(hint.get("descriptor_types", []))
    if not descriptor_types:
        return bool(values)

    choice_names = set(hint.get("choice_names", []))
    if "numeric" in descriptor_types and any(
        isinstance(value, (int, float)) and not isinstance(value, bool)
        for value in values
    ):
        return True
    if "boolean" in descriptor_types and any(
        isinstance(value, bool) for value in values
    ):
        return True
    if descriptor_types.intersection({"text", "selection"}):
        return any(
            isinstance(value, str)
            and bool(value.strip())
            and value.strip() not in choice_names
            for value in values
        )
    return False


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
    language: RuntimeValidationLanguage = DEFAULT_LANGUAGE,
) -> FindingsValidatorExecutionDataDict:
    _validate_language(language)
    normalized_findings = _normalize_reported_findings(reported_findings)
    target_finding = validator.finding
    matched_occurrences = [
        finding
        for finding in normalized_findings
        if finding["finding"] == target_finding
    ]

    issues: list[RuntimeValidationIssueDataDict] = []
    missing_required_classifications: list[str] = []
    triggered_occurrences = 0

    if validator.operator == "exists":
        ok = len(matched_occurrences) > 0
        if not ok:
            issues.append(
                _build_issue(
                    code="finding_not_present",
                    message=_runtime_message(
                        "finding_not_present",
                        language,
                        target_finding=target_finding,
                        name=validator.name,
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
                    message=_runtime_message(
                        "finding_present_but_should_be_missing",
                        language,
                        target_finding=target_finding,
                        name=validator.name,
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
                    message=_runtime_message(
                        "invalid_conditional_validator_definition",
                        language,
                        name=validator.name,
                    ),
                    validator_name=validator.name,
                    validator_kind="findings_validator",
                )
            )
        else:
            for occurrence_index, occurrence in enumerate(matched_occurrences):
                condition_result, missing_condition_data = _condition_evaluation(
                    condition, occurrence["classifications"]
                )
                if condition_result is None:
                    ok = False
                    issues.append(
                        _build_issue(
                            code="missing_data_requirement",
                            message=_runtime_message(
                                "missing_data_requirement",
                                language,
                                name=validator.name,
                                requirements=", ".join(missing_condition_data),
                            ),
                            validator_name=validator.name,
                            validator_kind="findings_validator",
                            level="warning",
                            details={
                                "occurrence_index": occurrence_index,
                                "missing_condition_classifications": (
                                    missing_condition_data
                                ),
                            },
                        )
                    )
                    continue
                if condition_result is False:
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
                if not missing and not missing_generic:
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
                        message=_runtime_message(
                            "missing_required_classification",
                            language,
                            name=validator.name,
                            requirements=", ".join(missing or missing_generic),
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
                message=_runtime_message(
                    "unsupported_operator", language, operator=validator.operator
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
    language: RuntimeValidationLanguage = DEFAULT_LANGUAGE,
) -> ClassificationValidatorExecutionDataDict:
    _validate_language(language)
    normalized_findings = _normalize_reported_findings(reported_findings)
    target_finding = validator.finding
    target_classification = validator.classification
    matched_occurrences = [
        finding
        for finding in normalized_findings
        if finding["finding"] == target_finding
    ]

    issues: list[RuntimeValidationIssueDataDict] = []
    triggered_occurrences = 0
    hint = _build_classification_hint(
        validator=validator,
        classifications=classifications,
        classification_choices=classification_choices,
        classification_choice_descriptors=classification_choice_descriptors,
    )

    if validator.operator == "exists":
        if not matched_occurrences:
            ok = validator.precedence == "optional"
            if not ok:
                issues.append(
                    _build_issue(
                        code="finding_not_present_for_classification_validator",
                        message=_runtime_message(
                            "finding_not_present_for_classification_validator",
                            language,
                            target_finding=target_finding,
                            name=validator.name,
                        ),
                        validator_name=validator.name,
                        validator_kind="classification_validator",
                    )
                )
        else:
            ok = any(
                _classification_has_evaluable_value(
                    occurrence["classifications"].get(target_classification, []),
                    hint,
                )
                for occurrence in matched_occurrences
            )
            if not ok:
                requires_descriptor = bool(hint.get("descriptor_types"))
                issues.append(
                    _build_issue(
                        code=(
                            "classification_value_not_present"
                            if requires_descriptor
                            else "classification_not_present"
                        ),
                        message=(
                            _runtime_message(
                                "classification_value_not_present",
                                language,
                                target_classification=target_classification,
                                name=validator.name,
                            )
                            if requires_descriptor
                            else _runtime_message(
                                "classification_not_present",
                                language,
                                target_classification=target_classification,
                                name=validator.name,
                            )
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
                    message=_runtime_message(
                        "classification_present_but_should_be_missing",
                        language,
                        target_classification=target_classification,
                        name=validator.name,
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
                    message=_runtime_message(
                        "invalid_conditional_validator_definition",
                        language,
                        name=validator.name,
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
                        message=_runtime_message(
                            "finding_not_present_for_classification_validator",
                            language,
                            target_finding=target_finding,
                            name=validator.name,
                        ),
                        validator_name=validator.name,
                        validator_kind="classification_validator",
                    )
                )
            else:
                ok = True
                for occurrence_index, occurrence in enumerate(matched_occurrences):
                    condition_result, missing_condition_data = _condition_evaluation(
                        condition, occurrence["classifications"]
                    )
                    if condition_result is None:
                        ok = False
                        issues.append(
                            _build_issue(
                                code="missing_data_requirement",
                                message=_runtime_message(
                                    "missing_data_requirement",
                                    language,
                                    name=validator.name,
                                    requirements=", ".join(missing_condition_data),
                                ),
                                validator_name=validator.name,
                                validator_kind="classification_validator",
                                level="warning",
                                details={
                                    "occurrence_index": occurrence_index,
                                    "missing_condition_classifications": (
                                        missing_condition_data
                                    ),
                                },
                            )
                        )
                        continue
                    if condition_result is False:
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
                            message=_runtime_message(
                                "conditional_classification_requirement",
                                language,
                                name=validator.name,
                                classification=target_classification,
                                additional=_runtime_message(
                                    "additional_requirements",
                                    language,
                                    requirements=", ".join(missing_requirements),
                                )
                                if missing_requirements
                                else "",
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
                message=_runtime_message(
                    "unsupported_operator", language, operator=validator.operator
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
    language: RuntimeValidationLanguage = DEFAULT_LANGUAGE,
) -> InterventionValidatorExecutionDataDict:
    _validate_language(language)
    normalized_findings = _normalize_reported_findings(reported_findings)
    matched_occurrences = [
        finding
        for finding in normalized_findings
        if finding["finding"] == validator.finding
    ]
    issues: list[RuntimeValidationIssueDataDict] = []
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
                    message=_runtime_message(
                        "intervention_not_present",
                        language,
                        intervention=validator.intervention,
                        name=validator.name,
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
                    message=_runtime_message(
                        "intervention_present_but_should_be_missing",
                        language,
                        intervention=validator.intervention,
                        name=validator.name,
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
                    message=_runtime_message(
                        "invalid_conditional_validator_definition",
                        language,
                        name=validator.name,
                    ),
                    validator_name=validator.name,
                    validator_kind="intervention_validator",
                )
            )
        else:
            for occurrence_index, occurrence in enumerate(matched_occurrences):
                condition_result, missing_condition_data = _condition_evaluation(
                    condition, occurrence["classifications"]
                )
                if condition_result is None:
                    ok = False
                    issues.append(
                        _build_issue(
                            code="missing_data_requirement",
                            message=_runtime_message(
                                "missing_data_requirement",
                                language,
                                name=validator.name,
                                requirements=", ".join(missing_condition_data),
                            ),
                            validator_name=validator.name,
                            validator_kind="intervention_validator",
                            level="warning",
                            details={
                                "occurrence_index": occurrence_index,
                                "missing_condition_classifications": (
                                    missing_condition_data
                                ),
                            },
                        )
                    )
                    continue
                if condition_result is False:
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
                        message=_runtime_message(
                            "missing_required_intervention",
                            language,
                            name=validator.name,
                            intervention=validator.intervention,
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
                message=_runtime_message(
                    "unsupported_operator", language, operator=validator.operator
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
    language: RuntimeValidationLanguage = DEFAULT_LANGUAGE,
) -> UnitValidatorExecutionDataDict:
    _validate_language(language)
    normalized_findings = _normalize_reported_findings(reported_findings)
    matched_occurrences = [
        finding
        for finding in normalized_findings
        if finding["finding"] == validator.finding
    ]
    issues: list[RuntimeValidationIssueDataDict] = []
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
                    message=_runtime_message(
                        "unit_not_present",
                        language,
                        unit=validator.unit,
                        name=validator.name,
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
                    message=_runtime_message(
                        "unit_present_but_should_be_missing",
                        language,
                        unit=validator.unit,
                        name=validator.name,
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
                    message=_runtime_message(
                        "invalid_conditional_validator_definition",
                        language,
                        name=validator.name,
                    ),
                    validator_name=validator.name,
                    validator_kind="unit_validator",
                )
            )
        else:
            for occurrence_index, occurrence in enumerate(matched_occurrences):
                condition_result, missing_condition_data = _condition_evaluation(
                    condition, occurrence["classifications"]
                )
                if condition_result is None:
                    ok = False
                    issues.append(
                        _build_issue(
                            code="missing_data_requirement",
                            message=_runtime_message(
                                "missing_data_requirement",
                                language,
                                name=validator.name,
                                requirements=", ".join(missing_condition_data),
                            ),
                            validator_name=validator.name,
                            validator_kind="unit_validator",
                            level="warning",
                            details={
                                "occurrence_index": occurrence_index,
                                "missing_condition_classifications": (
                                    missing_condition_data
                                ),
                            },
                        )
                    )
                    continue
                if condition_result is False:
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
                        message=_runtime_message(
                            "missing_required_unit",
                            language,
                            name=validator.name,
                            unit=validator.unit,
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
                message=_runtime_message(
                    "unsupported_operator", language, operator=validator.operator
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
    language: RuntimeValidationLanguage = DEFAULT_LANGUAGE,
) -> ReportTemplateRuntimeValidationResultDataDict:
    _validate_language(language)
    normalized_findings = _normalize_reported_findings(reported_findings)

    classification_cache: dict[str, ClassificationValidatorExecutionDataDict] = {}
    intervention_cache: dict[str, InterventionValidatorExecutionDataDict] = {}
    findings_cache: dict[str, FindingsValidatorExecutionDataDict] = {}
    exam_cache: dict[str, ExaminationValidatorExecutionDataDict] = {}
    unit_cache: dict[str, UnitValidatorExecutionDataDict] = {}

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
                        message=_runtime_message(
                            "unknown_classification_validator_reference",
                            language,
                            validator_name=validator_name,
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
            language=language,
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
                        message=_runtime_message(
                            "unknown_findings_validator_reference",
                            language,
                            validator_name=validator_name,
                        ),
                        validator_name=validator_name,
                        validator_kind="findings_validator",
                    )
                ],
            )
            findings_cache[validator_name] = result
            return result

        result = evaluate_findings_validator_runtime(
            validator,
            reported_findings=normalized_findings,
            language=language,
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
                        message=_runtime_message(
                            "unknown_intervention_validator_reference",
                            language,
                            validator_name=validator_name,
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
            language=language,
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
                        message=_runtime_message(
                            "unknown_unit_validator_reference",
                            language,
                            validator_name=validator_name,
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
            language=language,
        )
        unit_cache[validator_name] = result
        return result

    def evaluate_examination_validator_by_name(
        validator_name: str,
        stack: list[str],
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
                        message=_runtime_message(
                            "circular_examination_validator_dependency",
                            language,
                            cycle=" -> ".join(cycle),
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
                        message=_runtime_message(
                            "unknown_examination_validator_reference",
                            language,
                            validator_name=validator_name,
                        ),
                        validator_name=validator_name,
                        validator_kind="examination_validator",
                    )
                ],
            )
            exam_cache[validator_name] = result
            return result

        stack.append(validator_name)
        findings_status: list[ExaminationValidatorDependencyStatusDataDict] = []
        exams_status: list[ExaminationValidatorDependencyStatusDataDict] = []
        issues: list[RuntimeValidationIssueDataDict] = []
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
                    message=_runtime_message(
                        "failed_finding_validator_dependency",
                        language,
                        validator_name=validator_name,
                        dep_name=dep_name,
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
                    message=_runtime_message(
                        "failed_examination_validator_dependency",
                        language,
                        validator_name=validator_name,
                        dep_name=dep_name,
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

    issues: list[RuntimeValidationIssueDataDict] = []
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
    "ClassificationValidatorExecutionDataDict",
    "ExaminationValidatorDependencyStatusDataDict",
    "ExaminationValidatorExecutionDataDict",
    "FindingsValidatorExecutionDataDict",
    "InterventionValidatorExecutionDataDict",
    "ReportTemplateRuntimeValidationResultDataDict",
    "RuntimeValidationIssueDataDict",
    "RuntimeValidationLanguage",
    "UnitValidatorExecutionDataDict",
    "evaluate_classification_validator_runtime",
    "evaluate_findings_validator_runtime",
    "evaluate_intervention_validator_runtime",
    "evaluate_report_template_validators_runtime",
    "evaluate_unit_validator_runtime",
]
