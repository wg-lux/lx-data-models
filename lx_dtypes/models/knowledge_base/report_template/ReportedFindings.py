"""Shared normalization of reported finding payloads."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from enum import Enum
from typing import TypedDict

from lx_dtypes.models.knowledge_base.validators.ValueTypes import (
    ValidationScalar,
    ValidationValue,
)


class _RuntimeFindingOccurrence(TypedDict):
    finding: str
    classifications: dict[str, list[ValidationScalar]]
    classification_units: dict[str, list[str]]
    interventions: list[str]


def _as_str_list(value: object) -> list[str]:
    if value in (None, ""):
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, Sequence):
        result: list[str] = []
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
    if isinstance(value, Enum):
        return _normalize_identifier(value.value)
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
    target: dict[str, list[ValidationScalar]],
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
    target: dict[str, list[str]], classification_name: object, unit_name: object
) -> None:
    normalized_name = _normalize_identifier(classification_name)
    normalized_unit = _normalize_identifier(unit_name)
    if not normalized_name or not normalized_unit:
        return
    bucket = target.setdefault(normalized_name, [])
    bucket.append(normalized_unit)


def _normalize_interventions(raw: object) -> list[str]:
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

    interventions: list[str] = []
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
) -> tuple[dict[str, list[ValidationScalar]], dict[str, list[str]]]:
    normalized: dict[str, list[ValidationScalar]] = {}
    units: dict[str, list[str]] = {}
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


def _normalize_classification_units(raw: object) -> dict[str, list[str]]:
    normalized: dict[str, list[str]] = {}
    if not isinstance(raw, Mapping):
        return normalized

    for classification_name, unit_values in raw.items():
        if isinstance(unit_values, list):
            for unit_name in unit_values:
                _add_classification_unit(normalized, classification_name, unit_name)
            continue
        _add_classification_unit(normalized, classification_name, unit_values)

    return normalized


def _normalize_reported_findings(
    reported_findings: Sequence[Mapping[str, object]] | None,
) -> list[_RuntimeFindingOccurrence]:
    if not reported_findings:
        return []

    occurrences: list[_RuntimeFindingOccurrence] = []
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
        classification_units.update(
            _normalize_classification_units(finding_payload.get("classification_units"))
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
