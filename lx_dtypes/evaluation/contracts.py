"""Blocking and advisory parsing through the owning model's validation rules.

Expected validation failures become reports. Programming errors and broken
knowledge-base configuration still propagate; no persistence is performed.
"""

from typing import Literal

from pydantic import BaseModel, ValidationError

from lx_dtypes.language import (
    DEFAULT_LANGUAGE,
    LanguageCode,
    load_message_catalogue,
    validate_language,
)
from lx_dtypes.models.contracts.validation import (
    ContractValidationResult,
    ValidationIssue,
    ValidationReport,
)


def _issue(
    code: str,
    *,
    source: Literal["contract", "terminology", "study"] = "terminology",
    path: tuple[str | int, ...] = (),
    language: LanguageCode = DEFAULT_LANGUAGE,
) -> ValidationIssue:
    messages = load_message_catalogue("validation_messages.yml")[language]
    return ValidationIssue(
        code=code,
        message=messages.get(code, messages["contract.invalid"]),
        source=source,
        path=path,
    )


def parse_contract[T: BaseModel](model: type[T], payload: object) -> T:
    """Revalidate supplied instances and raise on invalid input."""
    return model.model_validate(
        payload.model_dump(mode="python", round_trip=True)
        if isinstance(payload, BaseModel)
        else payload
    )


def parse_contract_json[T: BaseModel](model: type[T], payload: str | bytes) -> T:
    """Strict JSON boundary with the owning model's date/UUID parsing semantics."""
    return model.model_validate_json(payload)


def validate_contract[T: BaseModel](
    model: type[T], payload: object, *, language: LanguageCode = DEFAULT_LANGUAGE
) -> ContractValidationResult[T]:
    """Collect schema errors without echoing submitted values or exception context.

    Parsing follows the owning model's strictness and validators. Pass Python
    data here; use ``validate_contract_json`` for JSON text.
    """
    return _validate_contract(model, payload, language=language, json_input=False)


def validate_contract_json[T: BaseModel](
    model: type[T], payload: str | bytes, *, language: LanguageCode = DEFAULT_LANGUAGE
) -> ContractValidationResult[T]:
    """Parse JSON using the owning model's native JSON rules and the same findings.

    Strict models accept ISO dates/UUIDs in JSON while preserving their strict
    Python-object boundary. Invalid JSON is a contract finding, not a fallback.
    """
    return _validate_contract(model, payload, language=language, json_input=True)


def _validate_contract[T: BaseModel](
    model: type[T], payload: object, *, language: LanguageCode, json_input: bool
) -> ContractValidationResult[T]:
    validate_language(language)
    try:
        # Revalidate model instances too, including mutable ledger models.
        if json_input:
            if not isinstance(payload, (str, bytes)):
                raise TypeError("JSON contract input must be text or bytes")
            value = parse_contract_json(model, payload)
        else:
            value = parse_contract(model, payload)
    except ValidationError as error:
        return ContractValidationResult[T](
            value=None,
            report=ValidationReport(
                issues=tuple(
                    _issue(
                        f"contract.{item['type']}",
                        source="contract",
                        path=item["loc"],
                        language=language,
                    )
                    for item in error.errors(
                        include_input=False, include_context=False, include_url=False
                    )
                )
            ),
        )
    return ContractValidationResult[T](value=value, report=ValidationReport())


__all__ = [
    "parse_contract",
    "parse_contract_json",
    "validate_contract",
    "validate_contract_json",
]
