"""FHIR Observation component projection and terminology-validated finding exchange."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from math import isfinite
from typing import Literal, TypedDict

from lx_dtypes.language import DEFAULT_LANGUAGE
from lx_dtypes.language import validate_language as _validate_language
from lx_dtypes.models.contracts.fhir_clinical import (
    FhirCodeableConcept,
    FhirObservationComponent,
)
from lx_dtypes.models.knowledge_base.report_template.ReportedFindings import (
    _normalize_identifier,
    _normalize_reported_findings,
)
from lx_dtypes.models.knowledge_base.validators.FindingTerminologyValidation import (
    validate_reported_findings_against_terminology,
)
from lx_dtypes.models.knowledge_base.validators.RuntimeIssues import (
    RuntimeValidationLanguage,
)
from lx_dtypes.models.knowledge_base.validators.ValidatorRuntimeDataDict import (
    RuntimeValidationIssueDataDict,
)
from lx_dtypes.models.knowledge_base.validators.ValueTypes import (
    ValidationScalar,
)

from ..classification.Classification import Classification
from ..classification_choice.ClassificationChoice import ClassificationChoice
from ..finding._Finding import Finding
from ..unit.Unit import Unit


class FhirTerminologyValidatedFindingResultDataDict(TypedDict):
    ok: bool
    reported_findings: list[dict[str, object]]
    observations: list[dict[str, object]]
    issues: list[RuntimeValidationIssueDataDict]


def _slug(value: object) -> str:
    token = _normalize_identifier(value).lower()
    token = token.replace("_", "-")
    cleaned = []
    previous_dash = False
    for char in token:
        if char.isalnum():
            cleaned.append(char)
            previous_dash = False
            continue
        if not previous_dash:
            cleaned.append("-")
            previous_dash = True
    return "".join(cleaned).strip("-") or "unknown"


def _coding(system: str, code: object, display: object | None = None) -> dict[str, str]:
    coding = {"system": system, "code": _slug(code)}
    display_value = _normalize_identifier(display if display is not None else code)
    if display_value:
        coding["display"] = display_value
    return coding


def _first_coding_display(value: object) -> str:
    if not isinstance(value, Mapping):
        return _normalize_identifier(value)
    codings = value.get("coding")
    if isinstance(codings, Sequence) and not isinstance(codings, (str, bytes)):
        for coding in codings:
            if isinstance(coding, Mapping):
                display = _normalize_identifier(coding.get("display"))
                if display:
                    return display
                code = _normalize_identifier(coding.get("code"))
                if code:
                    return code.replace("-", "_")
    return _normalize_identifier(value)


def _quantity_unit(value: object) -> str | None:
    if not isinstance(value, Mapping):
        return None
    unit = _normalize_identifier(value.get("unit"))
    if unit:
        return unit
    code = _normalize_identifier(value.get("code"))
    return code or None


def _observation_value(component: FhirObservationComponent) -> ValidationScalar:
    if component.valueCodeableConcept is not None:
        return _first_coding_display(component.valueCodeableConcept.model_dump())
    if component.valueQuantity is not None:
        return component.valueQuantity.value
    for value in (
        component.valueString,
        component.valueBoolean,
        component.valueInteger,
        component.valueDecimal,
    ):
        if value is not None:
            return value
    raise ValueError("Observation component requires a supported value[x]")


def import_fhir_observations_to_reported_findings(
    observations: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    """Convert FHIR Observation resources into runtime reported-finding payloads."""

    reported_findings: list[dict[str, object]] = []
    for observation in observations:
        if observation.get("resourceType") != "Observation":
            raise ValueError("Expected an Observation resource")
        FhirCodeableConcept.model_validate(observation.get("code"))
        finding_name = _first_coding_display(observation.get("code"))
        if not finding_name:
            continue

        classifications: list[dict[str, object]] = []
        raw_components = observation.get("component", [])
        if not isinstance(raw_components, (list, tuple)):
            raise TypeError("Observation.component must be an array")
        components = raw_components
        for component in components:
            if not isinstance(component, Mapping):
                raise TypeError("Observation.component entries must be objects")
            validated_component = FhirObservationComponent.model_validate(component)
            classification_name = _first_coding_display(component.get("code"))
            if not classification_name:
                continue
            classification_payload: dict[str, object] = {
                "classification": classification_name,
                "value": _observation_value(validated_component),
            }
            unit = _quantity_unit(component.get("valueQuantity"))
            if unit:
                classification_payload["unit"] = unit
            classifications.append(classification_payload)

        reported_findings.append(
            {
                "finding": finding_name,
                "classifications": classifications,
                "interventions": [],
            }
        )
    return reported_findings


def _component_value_for_classification(
    value: ValidationScalar,
    *,
    classification_name: str,
    unit: str | None,
    base_url: str,
) -> dict[str, object]:
    if isinstance(value, float) and not isfinite(value):
        raise ValueError("Observation numeric values must be finite")
    if unit and isinstance(value, (int, float)) and not isinstance(value, bool):
        return {
            "valueQuantity": {
                "value": value,
                "unit": unit,
                "system": "http://unitsofmeasure.org",
                "code": unit,
            }
        }
    if isinstance(value, bool):
        return {"valueBoolean": value}
    if isinstance(value, (int, float)):
        # R4 Observation has no valueDecimal choice. Unitless numbers are
        # represented as Quantity so fractional values remain valid FHIR.
        return {"valueQuantity": {"value": value}}
    value_text = _normalize_identifier(value)
    if not value_text:
        return {"valueBoolean": True}
    return {
        "valueCodeableConcept": {
            "coding": [
                _coding(
                    f"{base_url}/CodeSystem/lx-classification-choice-cs",
                    value_text,
                    value_text,
                )
            ],
            "text": value_text,
        }
    }


def export_reported_findings_to_fhir_observations(
    reported_findings: Sequence[Mapping[str, object]],
    *,
    base_url: str = "https://wg-lux.de/fhir",
    status: Literal["preliminary", "final"] = "preliminary",
) -> list[dict[str, object]]:
    """Convert runtime reported-finding payloads into FHIR Observation resources."""

    if status not in {"preliminary", "final"}:
        raise ValueError("Observation export status must be preliminary or final")
    observations: list[dict[str, object]] = []
    for occurrence in _normalize_reported_findings(reported_findings):
        finding_name = occurrence["finding"]
        components: list[dict[str, object]] = []
        for classification_name, values in occurrence["classifications"].items():
            units = occurrence["classification_units"].get(classification_name, [])
            unit = units[0] if units else None
            for value in values:
                component: dict[str, object] = {
                    "code": {
                        "coding": [
                            _coding(
                                f"{base_url}/CodeSystem/lx-classification-cs",
                                classification_name,
                                classification_name,
                            )
                        ],
                        "text": classification_name,
                    }
                }
                component.update(
                    _component_value_for_classification(
                        value,
                        classification_name=classification_name,
                        unit=unit,
                        base_url=base_url,
                    )
                )
                components.append(component)

        observations.append(
            {
                "resourceType": "Observation",
                "status": status,
                "code": {
                    "coding": [
                        _coding(
                            f"{base_url}/CodeSystem/lx-finding-cs",
                            finding_name,
                            finding_name,
                        )
                    ],
                    "text": finding_name,
                },
                "component": components,
            }
        )
    return observations


def import_terminology_validated_fhir_observations(
    observations: Sequence[Mapping[str, object]],
    *,
    findings: Mapping[str, Finding],
    classifications: Mapping[str, Classification],
    classification_choices: Mapping[str, ClassificationChoice],
    units: Mapping[str, Unit],
    language: RuntimeValidationLanguage = DEFAULT_LANGUAGE,
) -> FhirTerminologyValidatedFindingResultDataDict:
    """Import FHIR Observations and validate them against YAML KB terminology."""

    _validate_language(language)
    reported_findings = import_fhir_observations_to_reported_findings(observations)
    issues = validate_reported_findings_against_terminology(
        reported_findings,
        findings=findings,
        classifications=classifications,
        classification_choices=classification_choices,
        units=units,
        language=language,
    )
    return FhirTerminologyValidatedFindingResultDataDict(
        ok=not issues,
        reported_findings=reported_findings,
        observations=[dict(observation) for observation in observations],
        issues=issues,
    )


def export_terminology_validated_fhir_observations(
    reported_findings: Sequence[Mapping[str, object]],
    *,
    findings: Mapping[str, Finding],
    classifications: Mapping[str, Classification],
    classification_choices: Mapping[str, ClassificationChoice],
    units: Mapping[str, Unit],
    base_url: str = "https://wg-lux.de/fhir",
    language: RuntimeValidationLanguage = DEFAULT_LANGUAGE,
) -> FhirTerminologyValidatedFindingResultDataDict:
    """Validate runtime findings against YAML KB terminology and export FHIR."""

    _validate_language(language)
    observations = export_reported_findings_to_fhir_observations(
        reported_findings,
        base_url=base_url,
    )
    issues = validate_reported_findings_against_terminology(
        reported_findings,
        findings=findings,
        classifications=classifications,
        classification_choices=classification_choices,
        units=units,
        language=language,
    )
    return FhirTerminologyValidatedFindingResultDataDict(
        ok=not issues,
        reported_findings=[dict(item) for item in reported_findings],
        observations=observations,
        issues=issues,
    )
