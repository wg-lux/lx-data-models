"""Shared localized issue construction for runtime and terminology validation."""

from __future__ import annotations

from typing import Literal

from lx_dtypes.language import LanguageCode, load_message_catalogue
from lx_dtypes.models.knowledge_base.validators.ValidatorRuntimeDataDict import (
    RuntimeValidationIssueDataDict,
)
from lx_dtypes.models.knowledge_base.validators.ValueTypes import (
    ValidationIssueDetails,
)

# Preserve the existing public alias.
RuntimeValidationLanguage = LanguageCode


def _runtime_messages() -> dict[RuntimeValidationLanguage, dict[str, str]]:
    return load_message_catalogue("validator_runtime_messages.yml")


def _runtime_message(
    key: str, language: RuntimeValidationLanguage, **values: str
) -> str:
    return _runtime_messages()[language][key].format(**values)


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
        details=details or {},
    )
    return issue
