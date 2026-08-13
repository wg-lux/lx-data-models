import json
from pathlib import Path
from typing import Any, cast

import pytest
from pydantic import ValidationError

from lx_dtypes.models.contracts.fhir_clinical import (
    FhirClinicalBundle,
    FhirDiagnosticReport,
    FhirObservation,
    FhirObservationComponent,
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
