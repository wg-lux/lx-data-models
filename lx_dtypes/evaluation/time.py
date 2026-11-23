"""Time-offset assessment using the canonical contract/terminology findings."""

from typing import TYPE_CHECKING

from lx_dtypes.language import DEFAULT_LANGUAGE, LanguageCode
from lx_dtypes.models.contracts.validation import (
    SemanticValidationError,
    ValidationReport,
)
from lx_dtypes.models.ledger.p_time_offset import PTimeOffset

from .contracts import _issue, validate_contract

if TYPE_CHECKING:
    from lx_dtypes.models.interface.KnowledgeBase import KnowledgeBase


def assess_time_offset(
    knowledge_base: "KnowledgeBase",
    payload: object,
    *,
    language: LanguageCode = DEFAULT_LANGUAGE,
) -> ValidationReport:
    """Validate a time-offset payload against a knowledge base without raising.

    The payload is first validated as a
    :class:`~lx_dtypes.models.ledger.p_time_offset.PTimeOffset` contract and
    then checked against the knowledge base's time references.

    Args:
        knowledge_base: Knowledge base that defines the time references.
        payload: Untrusted time-offset data.
        language: Language for issue messages.

    Returns:
        A report that records the knowledge-base identity and any issues.
    """
    parsed = validate_contract(PTimeOffset, payload, language=language)
    identity = knowledge_base.config.knowledge_base_identity
    if parsed.value is None:
        return ValidationReport(
            issues=parsed.report.issues, knowledge_base_identity=identity
        )
    try:
        knowledge_base.validate_time_offset(parsed.value)
    except SemanticValidationError as error:
        return ValidationReport(
            issues=(_issue(error.code, language=language),),
            knowledge_base_identity=identity,
        )
    return ValidationReport(knowledge_base_identity=identity)


__all__ = ["assess_time_offset"]
