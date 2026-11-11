"""Terminology and study evaluation delegated to the canonical KB engines."""

from typing import TYPE_CHECKING

from lx_dtypes.language import DEFAULT_LANGUAGE, LanguageCode
from lx_dtypes.models.contracts.validation import ValidationIssue, ValidationReport

from .contracts import _issue, validate_contract

if TYPE_CHECKING:
    from lx_dtypes.models.interface.KnowledgeBase import KnowledgeBase


def assess_examination(
    knowledge_base: "KnowledgeBase",
    payload: object,
    *,
    template_name: str | None = None,
    language: LanguageCode = DEFAULT_LANGUAGE,
) -> ValidationReport:
    """Assess ledger data against its pinned terminology and optional study rules.

    Incomplete identity is a warning for legacy ledger records. A conflicting
    identity or semantic failure prevents study evaluation, not draft capture.
    Semantic admissibility reports the first failure from the existing strict
    engine; study evaluation returns all issues collected by that engine.
    """
    from lx_dtypes.models.interface.KnowledgeBase import SemanticAdmissibilityError
    from lx_dtypes.models.ledger.p_examination.Pydantic import PExamination

    identity = knowledge_base.config.knowledge_base_identity
    parsed = validate_contract(PExamination, payload, language=language)
    if parsed.value is None:
        return ValidationReport(
            issues=parsed.report.issues, knowledge_base_identity=identity
        )
    examination = parsed.value
    issues: list[ValidationIssue] = []
    supplied = (examination.knowledge_base_module, examination.knowledge_base_version)
    expected = (identity.knowledge_base_module, identity.knowledge_base_version)
    # A known conflicting component remains an error even if the other is absent.
    if any(
        actual is not None and actual != target
        for actual, target in zip(supplied, expected)
    ):
        issues.append(_issue("terminology.identity_mismatch", language=language))
    elif None in supplied:
        issues.append(
            _issue("terminology.identity_missing", language=language).model_copy(
                update={"level": "warning"}
            )
        )
    if (
        template_name is not None
        and template_name not in knowledge_base.report_template
    ):
        issues.append(_issue("terminology.template_unknown", language=language))
    if any(issue.level == "error" for issue in issues):
        return ValidationReport(issues=tuple(issues), knowledge_base_identity=identity)
    try:
        if template_name is None:
            knowledge_base.assert_examination_admissibility(examination)
        else:
            runtime = knowledge_base.evaluate_report_template_validators(
                template_name, p_examination=examination, language=language
            )
            issues.extend(
                ValidationIssue(
                    code=item["code"],
                    message=item["message"],
                    level=item["level"],
                    source="study",
                    validator_name=item["validator_name"],
                )
                for item in runtime["issues"]
            )
    except SemanticAdmissibilityError:
        issues.append(_issue("terminology.inadmissible", language=language))
        return ValidationReport(issues=tuple(issues), knowledge_base_identity=identity)
    return ValidationReport(
        issues=tuple(issues),
        knowledge_base_identity=identity,
        study_evaluated=template_name is not None,
    )


__all__ = ["assess_examination"]
