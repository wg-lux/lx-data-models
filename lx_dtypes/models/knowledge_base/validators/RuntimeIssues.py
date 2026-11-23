"""Shared localized issue construction for runtime and terminology validation."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any, Literal

from lx_dtypes.language import LanguageCode, load_message_catalogue
from lx_dtypes.models.base.app_base_model.pydantic.AppBaseModelNamesUUIDTags import (
    AppBaseModelNamesUUIDTags,
)
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


def _runtime_display_names(
    language: RuntimeValidationLanguage,
    *collections: Iterable[AppBaseModelNamesUUIDTags],
) -> dict[str, str]:
    """Prefer a translation over identity-only defaults, in the requested language."""
    names: dict[str, str] = {}
    for collection in collections:
        for item in collection:
            translations = (item.name_de, item.name_en)
            if language == "en":
                translations = translations[::-1]
            names[item.name] = next(
                (
                    label.strip()
                    for label in translations
                    if label.strip() and label.strip() not in {item.name, "unknown"}
                ),
                item.name,
            )
    return names


_DISPLAY_NAME_FIELDS = ("name", "finding", "classification", "intervention", "unit")
_DISPLAY_NAME_LIST_FIELDS = ("missing_required_classifications",)
_DISPLAY_NAME_STATUS_FIELDS = (
    "finding_validator_status",
    "examination_validator_status",
)


def _with_display_names[Entry: Mapping[str, Any]](
    entry: Entry, display_names: Mapping[str, str]
) -> Entry:
    """Add the entry's identifier -> display-name map; machine fields stay unchanged."""
    identifiers: list[str] = [
        value
        for field in _DISPLAY_NAME_FIELDS
        if isinstance(value := entry.get(field), str) and value
    ]
    for field in _DISPLAY_NAME_LIST_FIELDS:
        identifiers.extend(v for v in entry.get(field) or [] if isinstance(v, str))
    for field in _DISPLAY_NAME_STATUS_FIELDS:
        identifiers.extend(
            status["name"]
            for status in entry.get(field) or []
            if isinstance(status.get("name"), str)
        )
    names = dict(entry.get("display_names") or {})
    names.update({value: display_names.get(value, value) for value in identifiers})
    entry["display_names"] = names  # type: ignore[index]
    return entry


def _runtime_message(
    key: str,
    language: RuntimeValidationLanguage,
    *,
    display_names: Mapping[str, str] | None = None,
    **values: str,
) -> str:
    names = display_names or {}

    def label(value: str) -> str:
        # Requirement references carry a type prefix; keep it only for unknown names.
        return names.get(value, names.get(value.split(":", 1)[-1], value))

    translated: dict[str, str] = {}
    for field, value in values.items():
        if field in {"requirements", "cycle"}:
            separator = " -> " if field == "cycle" else ", "
            translated[field] = separator.join(
                label(token) for token in value.split(separator)
            )
        elif field == "additional":
            translated[field] = value  # Already formatted by the nested message call.
        else:
            translated[field] = label(value)
    return _runtime_messages()[language][key].format(**translated)


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
