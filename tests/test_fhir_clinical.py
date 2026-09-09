import json
from pathlib import Path
from typing import Any, cast

import pytest
from pydantic import ValidationError

from lx_dtypes.models.contracts.fhir_clinical import (
    FhirClinicalBundle,
    FhirClinicalBundleEntry,
    FhirDiagnosticReport,
    FhirObservation,
    FhirObservationComponent,
    FhirPatient,
)
from lx_dtypes.models.knowledge_base.report_template.ValidatorRuntime import (
    export_reported_findings_to_fhir_observations,
    import_fhir_observations_to_reported_findings,
)

FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "fhir"
    / "clinical-examination-transaction.json"
)


def _fixture_payload() -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(FIXTURE_PATH.read_text(encoding="utf-8")))


def _fixture_bundle() -> FhirClinicalBundle:
    return FhirClinicalBundle.model_validate(_fixture_payload())


def test_clinical_fixture_parses_and_resolves_report_graph() -> None:
    bundle = _fixture_bundle()

    reports = bundle.resolved_reports()

    assert len(reports) == 1
    assert reports[0].patient.id == "example-patient"
    assert reports[0].report.id == "example-cbc-report"
    assert [item.id for item in reports[0].observations] == ["example-hemoglobin"]


def test_clinical_fixture_preserves_standard_fhir_values_and_extra_fields() -> None:
    bundle = _fixture_bundle()
    observation = next(
        entry.resource
        for entry in bundle.entry
        if isinstance(entry.resource, FhirObservation)
    )

    assert observation.valueQuantity is not None
    assert observation.valueQuantity.value == 13.4
    assert observation.valueQuantity.code == "g/dL"

    dumped = bundle.model_dump(mode="json", exclude_none=True)
    patient = next(
        entry["resource"]
        for entry in dumped["entry"]
        if entry["resource"]["resourceType"] == "Patient"
    )
    assert patient["name"][0]["family"] == "Mustermann"
    assert patient["identifier"][0]["value"] == "EXAMPLE-001"


def test_clinical_fixture_observation_components_roundtrip_through_lxdm() -> None:
    bundle = _fixture_bundle()
    observation = next(
        entry.resource
        for entry in bundle.entry
        if isinstance(entry.resource, FhirObservation)
    )
    observation_payload = observation.model_dump(mode="python", exclude_none=True)

    findings = import_fhir_observations_to_reported_findings([observation_payload])
    exported = export_reported_findings_to_fhir_observations(findings)

    assert findings == [
        {
            "finding": "Hemoglobin [Mass/volume] in Blood",
            "classifications": [
                {"classification": "result", "value": 13.4, "unit": "g/dL"}
            ],
            "interventions": [],
        }
    ]
    exported_components = exported[0]["component"]
    assert isinstance(exported_components, list)
    exported_component = FhirObservationComponent.model_validate(exported_components[0])
    exported_quantity = exported_component.valueQuantity
    assert exported_quantity is not None
    assert exported_quantity.model_dump(exclude_none=True) == {
        "value": 13.4,
        "unit": "g/dL",
        "system": "http://unitsofmeasure.org",
        "code": "g/dL",
    }
    # The generic clinical contract retains this standard value. The existing
    # LXDM bridge intentionally round-trips only finding/classification components.
    assert observation.valueQuantity is not None
    assert observation.valueQuantity.value == 13.4
    assert "valueQuantity" not in exported[0]


def test_clinical_models_reject_observation_without_coding() -> None:
    payload = _fixture_payload()
    observation = payload["entry"][1]["resource"]
    observation["code"] = {"text": "Hemoglobin"}

    with pytest.raises(ValidationError, match="coding"):
        FhirClinicalBundle.model_validate(payload)


def test_clinical_models_reject_missing_subject() -> None:
    payload = _fixture_payload()
    del payload["entry"][1]["resource"]["subject"]

    with pytest.raises(ValidationError, match="subject"):
        FhirClinicalBundle.model_validate(payload)


def test_clinical_link_validation_rejects_unresolved_report_result() -> None:
    bundle = _fixture_bundle()
    report = next(
        entry.resource
        for entry in bundle.entry
        if isinstance(entry.resource, FhirDiagnosticReport)
    )
    report.result[0].reference = "Observation/missing"

    with pytest.raises(ValueError, match="Unresolved FHIR reference"):
        bundle.validate_clinical_links()


def test_clinical_link_validation_rejects_wrong_subject_type() -> None:
    bundle = _fixture_bundle()
    observation = next(
        entry.resource
        for entry in bundle.entry
        if isinstance(entry.resource, FhirObservation)
    )
    observation.subject.reference = "Condition/example-anemia"

    with pytest.raises(ValueError, match="expected FhirPatient"):
        bundle.validate_clinical_links()


@pytest.mark.parametrize(
    "value",
    [
        {"valueBoolean": "false"},
        {"valueInteger": True},
        {"valueInteger": 1.5},
        {"valueInteger": 2**31},
        {"valueQuantity": {"value": "12.3"}},
        {"valueQuantity": {"value": True}},
        {"valueQuantity": {"value": float("nan")}},
        {"valueDecimal": float("inf")},
        {"valueBoolean": False, "valueRange": {"low": {"value": 1}}},
        {"valueBoolean": False, "dataAbsentReason": {"text": "unknown"}},
    ],
)
def test_fhir_rejects_coerced_nonfinite_or_ambiguous_values(
    value: dict[str, object],
) -> None:
    with pytest.raises(ValidationError):
        FhirObservationComponent.model_validate(
            {
                "code": {"coding": [{"system": "urn:synthetic", "code": "result"}]},
                **value,
            }
        )


def test_duplicate_patient_only_bundle_is_rejected() -> None:
    entry = FhirClinicalBundleEntry(
        resource=FhirPatient(resourceType="Patient", id="synthetic")
    )
    bundle = FhirClinicalBundle(
        resourceType="Bundle", type="collection", entry=[entry, entry]
    )
    with pytest.raises(ValueError, match="Duplicate FHIR reference"):
        bundle.validate_clinical_links()


def test_resolved_reports_indexes_once_and_does_not_cache_mutable_input(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0
    original = FhirClinicalBundle.resource_index

    def counted(self: FhirClinicalBundle):
        nonlocal calls
        calls += 1
        return original(self)

    monkeypatch.setattr(FhirClinicalBundle, "resource_index", counted)
    bundle = _fixture_bundle()
    bundle.resolved_reports()
    assert calls == 1
    bundle.entry[1].resource.id = "changed"
    bundle.entry[1].fullUrl = None
    with pytest.raises(ValueError, match="Unresolved FHIR reference"):
        bundle.resolved_reports()
    assert calls == 2


def test_fhir_import_rejects_invalid_values_instead_of_inventing_true() -> None:
    payload = {
        "resourceType": "Observation",
        "code": {"coding": [{"system": "urn:synthetic", "code": "finding"}]},
        "component": [
            {
                "code": {"coding": [{"system": "urn:synthetic", "code": "result"}]},
                "valueBoolean": "invalid",
            }
        ],
    }
    with pytest.raises(ValidationError):
        import_fhir_observations_to_reported_findings([payload])


def test_unitless_numeric_export_uses_r4_quantity() -> None:
    exported = export_reported_findings_to_fhir_observations(
        [
            {
                "finding": "synthetic",
                "classifications": [{"classification": "result", "value": 1.25}],
            }
        ]
    )
    assert exported[0]["status"] == "preliminary"
    assert exported[0]["component"] == [
        {
            "code": {
                "coding": [
                    {
                        "system": "https://wg-lux.de/fhir/CodeSystem/lx-classification-cs",
                        "code": "result",
                        "display": "result",
                    }
                ],
                "text": "result",
            },
            "valueQuantity": {"value": 1.25},
        }
    ]
    assert import_fhir_observations_to_reported_findings(exported)[0][
        "classifications"
    ] == [{"classification": "result", "value": 1.25}]


@pytest.mark.parametrize(
    "modifier",
    [
        {"modifierExtension": [{"url": "urn:unsupported", "valueBoolean": True}]},
        {"implicitRules": "urn:unsupported"},
    ],
)
def test_clinical_contract_rejects_uninterpreted_modifiers(
    modifier: dict[str, object],
) -> None:
    with pytest.raises(ValidationError, match="explicit profile support"):
        FhirPatient.model_validate(
            {"resourceType": "Patient", "id": "synthetic", **modifier}
        )


def test_null_choice_does_not_override_valid_false_value_on_import() -> None:
    findings = import_fhir_observations_to_reported_findings(
        [
            {
                "resourceType": "Observation",
                "code": {"coding": [{"system": "urn:synthetic", "code": "finding"}]},
                "component": [
                    {
                        "code": {
                            "coding": [{"system": "urn:synthetic", "code": "result"}]
                        },
                        "valueString": None,
                        "valueBoolean": False,
                    }
                ],
            }
        ]
    )
    assert findings[0]["classifications"] == [
        {"classification": "result", "value": False}
    ]


@pytest.mark.parametrize("identifier", ["bad/id", "with space", "x" * 65, ""])
def test_fhir_resource_identifiers_reject_invalid_syntax(identifier: str) -> None:
    with pytest.raises(ValidationError):
        FhirPatient(resourceType="Patient", id=identifier)


def test_final_observation_status_requires_explicit_request() -> None:
    exported = export_reported_findings_to_fhir_observations(
        [{"finding": "synthetic"}], status="final"
    )
    assert exported[0]["status"] == "final"
