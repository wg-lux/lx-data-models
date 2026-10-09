"""Validate reported findings against loaded knowledge-base terminology."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from lx_dtypes.language import DEFAULT_LANGUAGE
from lx_dtypes.language import validate_language as _validate_language
from lx_dtypes.models.knowledge_base.report_template.ReportedFindings import (
    _as_str_list,
    _normalize_identifier,
    _normalize_reported_findings,
)
from lx_dtypes.models.knowledge_base.validators.RuntimeIssues import (
    RuntimeValidationLanguage,
    _build_issue,
    _runtime_message,
)
from lx_dtypes.models.knowledge_base.validators.ValidatorRuntimeDataDict import (
    RuntimeValidationIssueDataDict,
)

from ..classification.Classification import Classification
from ..classification_choice.ClassificationChoice import ClassificationChoice
from ..finding._Finding import Finding
from ..unit.Unit import Unit


def validate_reported_findings_against_terminology(
    reported_findings: Sequence[Mapping[str, object]],
    *,
    findings: Mapping[str, Finding],
    classifications: Mapping[str, Classification],
    classification_choices: Mapping[str, ClassificationChoice],
    units: Mapping[str, Unit],
    language: RuntimeValidationLanguage = DEFAULT_LANGUAGE,
) -> list[RuntimeValidationIssueDataDict]:
    """Validate normalized findings against the currently loaded YAML terminology."""

    _validate_language(language)
    issues: list[RuntimeValidationIssueDataDict] = []
    for occurrence_index, occurrence in enumerate(
        _normalize_reported_findings(reported_findings)
    ):
        finding = findings.get(occurrence["finding"])
        if finding is None:
            issues.append(
                _build_issue(
                    code="unknown_finding",
                    message=_runtime_message(
                        "unknown_finding", language, finding=occurrence["finding"]
                    ),
                    validator_name="terminology",
                    validator_kind="template",
                    details={"occurrence_index": occurrence_index},
                )
            )
            continue

        allowed_classifications = set(_as_str_list(finding.classifications))
        for classification_name, values in occurrence["classifications"].items():
            classification = classifications.get(classification_name)
            if classification is None:
                issues.append(
                    _build_issue(
                        code="unknown_classification",
                        message=_runtime_message(
                            "unknown_classification",
                            language,
                            classification_name=classification_name,
                        ),
                        validator_name="terminology",
                        validator_kind="template",
                        details={"occurrence_index": occurrence_index},
                    )
                )
                continue
            if (
                allowed_classifications
                and classification_name not in allowed_classifications
            ):
                issues.append(
                    _build_issue(
                        code="classification_not_allowed_for_finding",
                        message=_runtime_message(
                            "classification_not_allowed_for_finding",
                            language,
                            classification_name=classification_name,
                            finding=occurrence["finding"],
                        ),
                        validator_name="terminology",
                        validator_kind="template",
                        details={"occurrence_index": occurrence_index},
                    )
                )

            allowed_choices = set(_as_str_list(classification.classification_choices))
            for value in values:
                value_name = _normalize_identifier(value)
                if (
                    value_name
                    and not isinstance(value, (bool, int, float))
                    and allowed_choices
                    and value_name not in allowed_choices
                    and value_name not in classification_choices
                ):
                    issues.append(
                        _build_issue(
                            code="classification_choice_not_allowed",
                            message=_runtime_message(
                                "classification_choice_not_allowed",
                                language,
                                value_name=value_name,
                                classification_name=classification_name,
                            ),
                            validator_name="terminology",
                            validator_kind="template",
                            details={"occurrence_index": occurrence_index},
                        )
                    )

        for classification_name, unit_names in occurrence[
            "classification_units"
        ].items():
            for unit_name in unit_names:
                if unit_name not in units:
                    issues.append(
                        _build_issue(
                            code="unknown_unit",
                            message=_runtime_message(
                                "unknown_unit", language, unit_name=unit_name
                            ),
                            validator_name="terminology",
                            validator_kind="template",
                            details={
                                "occurrence_index": occurrence_index,
                                "classification": classification_name,
                            },
                        )
                    )
    return issues
