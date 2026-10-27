from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any

import pytest

from lx_dtypes.models.ledger.medical import PatientMedication
from lx_dtypes.models.ledger.medical.epa import (
    ADD_EMP_ENTRY_PARAMETERS_PROFILE,
    EMP_IDENTIFIER_SYSTEM,
    EmpEntryContext,
    EpaProjectionError,
    project_emp_entry,
)

KVNR = "X110411319"
CONTEXT = EmpEntryContext(kvnr=KVNR, authored_on=date(2026, 12, 1))


def _project(medication: PatientMedication, context: EmpEntryContext) -> Any:
    # FHIR payloads are recursive JSON unions; tests navigate them untyped.
    return project_emp_entry(medication, context)


def _medication(**overrides: Any) -> PatientMedication:
    fields: dict[str, Any] = {
        "uuid": "6f2d1a52-6c1e-4c5b-9a59-1e0d2b3c4d5e",
        "patient": "patient-1",
        "medication": "Benazepril AL 20mg",
        "pzn": "04351736",
        "substances": [{"name": "Benazepril hydrochlorid", "strength": "20 mg"}],
        "dosing": {"morning": "1", "evening": "1"},
        "dosage_form_code": "FTA",
        "unit_code": "1",
    }
    fields.update(overrides)
    return PatientMedication(**fields)


def _extension(resource: dict[str, Any], suffix: str) -> dict[str, Any]:
    matches = [ext for ext in resource["extension"] if ext["url"].endswith(suffix)]
    assert len(matches) == 1
    return matches[0]


def test_projects_official_four_schema_example_shape() -> None:
    projection = _project(
        _medication(medication_indication="Bluthochdruck", notes="Schwindel möglich"),
        CONTEXT,
    )
    medication = projection.medication
    request = projection.medication_request

    assert _extension(medication, "/context-extension")["valueCode"] == "EMP"
    assert medication["code"]["coding"] == [
        {"system": "http://fhir.de/CodeSystem/ifa/pzn", "code": "04351736"}
    ]
    assert medication["form"]["coding"][0]["code"] == "FTA"
    assert (
        medication["ingredient"][0]["strength"]["extension"][0]["valueString"]
        == "20 mg"
    )

    assert request["intent"] == "plan"
    assert request["status"] == "active"
    assert request["authoredOn"] == "2026-12-01"
    assert request["medicationReference"] == {
        "reference": f"Medication/{medication['id']}"
    }
    assert (
        request["subject"]["identifier"]["system"] == "http://fhir.de/sid/gkv/kvid-10"
    )
    assert request["subject"]["identifier"]["value"] == KVNR
    # Matches the dosage of the gematik add-emp-entry example.
    assert request["dosageInstruction"] == [
        {
            "timing": {
                "repeat": {
                    "frequency": 2,
                    "period": 1,
                    "periodUnit": "d",
                    "when": ["MORN", "EVE"],
                }
            },
            "doseAndRate": [
                {
                    "doseQuantity": {
                        "value": 1,
                        "unit": "Stück",
                        "system": "https://fhir.kbv.de/CodeSystem/KBV_CS_SFHIR_BMP_DOSIEREINHEIT",
                        "code": "1",
                    }
                }
            ],
        }
    ]
    assert (
        _extension(request, "renderedDosageInstruction")["valueMarkdown"]
        == "1-0-1-0 Stück"
    )
    assert _extension(request, "GeneratedDosageInstructionsMeta")
    assert _extension(request, "reason-patient-instruction-extension")[
        "valueString"
    ] == ("Bluthochdruck")
    assert _extension(request, "patient-note-extension")["valueAnnotation"] == {
        "text": "Schwindel möglich"
    }


def test_projection_ids_are_deterministic() -> None:
    first = _project(_medication(), CONTEXT)
    second = _project(_medication(), CONTEXT)
    assert first == second
    assert first.medication["id"] != first.medication_request["id"]


def test_distinct_doses_split_into_one_dosage_per_value() -> None:
    projection = _project(
        _medication(dosing={"morning": "1/2", "noon": "1", "night": "1/2"}), CONTEXT
    )
    dosages = projection.medication_request["dosageInstruction"]
    assert [
        (d["doseAndRate"][0]["doseQuantity"]["value"], d["timing"]["repeat"]["when"])
        for d in dosages
    ] == [
        (0.5, ["MORN", "NIGHT"]),
        (1, ["NOON"]),
    ]
    assert [d["timing"]["repeat"]["frequency"] for d in dosages] == [2, 1]
    rendered = _extension(projection.medication_request, "renderedDosageInstruction")
    assert rendered["valueMarkdown"] == "1/2-1-0-1/2 Stück"


def test_comma_decimal_and_weekly_dosing() -> None:
    projection = _project(_medication(dosing={"morning": "1,5", "weekday": 3}), CONTEXT)
    (dosage,) = projection.medication_request["dosageInstruction"]
    assert dosage["timing"]["repeat"] == {
        "frequency": 1,
        "period": 1,
        "dayOfWeek": ["wed"],
        "periodUnit": "wk",
        "when": ["MORN"],
    }
    assert dosage["doseAndRate"][0]["doseQuantity"]["value"] == 1.5
    rendered = _extension(projection.medication_request, "renderedDosageInstruction")
    assert rendered["valueMarkdown"] == "mittwochs: 1,5-0-0-0 Stück"


def test_free_text_dosing_is_single_text_only_dosage() -> None:
    projection = _project(
        _medication(dosing={"free_text": "bei Bedarf"}, unit_code=None), CONTEXT
    )
    request = projection.medication_request
    assert request["dosageInstruction"] == [{"text": "bei Bedarf"}]
    assert not any("renderedDosage" in ext["url"] for ext in request["extension"])


def test_substance_only_entry_omits_code() -> None:
    projection = _project(
        _medication(
            medication=None, pzn=None, dosage_form_code=None, dosage_form="Tabl."
        ),
        CONTEXT,
    )
    assert "code" not in projection.medication
    assert projection.medication["form"] == {"text": "Tabl."}
    assert projection.medication["ingredient"][0]["itemCodeableConcept"] == {
        "text": "Benazepril hydrochlorid"
    }


def test_period_maps_to_effective_dose_period() -> None:
    projection = _project(
        _medication(
            start_at=datetime(2026, 12, 1, 8, tzinfo=UTC),
            end_at=datetime(2027, 1, 1, 8, tzinfo=UTC),
        ),
        CONTEXT,
    )
    period = _extension(projection.medication_request, "effectiveDosePeriod")[
        "valuePeriod"
    ]
    assert period == {
        "start": "2026-12-01T08:00:00+00:00",
        "end": "2027-01-01T08:00:00+00:00",
    }


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"medication": None, "pzn": None, "substances": []}, "trade name, PZN"),
        ({"dosage_form_code": "ZZZ"}, "Darreichungsform"),
        ({"dosing": {}, "notes": "x"}, "requires a dosage"),
        ({"unit_code": None, "unit": "Stk"}, "Dosiereinheit"),
        ({"dosing": {"morning": "1/3"}}, "exact decimal"),
        ({"dosing": {}, "dosage": "1-0-1"}, "legacy dosage"),
        ({"active": False}, "explicit eMP status"),
    ],
)
def test_fails_closed_instead_of_guessing(
    overrides: dict[str, Any], message: str
) -> None:
    with pytest.raises(EpaProjectionError, match=message):
        _project(_medication(**overrides), CONTEXT)


def test_inactive_entry_uses_explicit_status() -> None:
    context = EmpEntryContext(
        kvnr=KVNR, authored_on=date(2026, 12, 1), status="completed"
    )
    projection = _project(_medication(active=False), context)
    assert projection.medication_request["status"] == "completed"
    with pytest.raises(EpaProjectionError, match="contradicts"):
        _project(
            _medication(active=False),
            EmpEntryContext(kvnr=KVNR, authored_on=date(2026, 12, 1), status="active"),
        )


def test_context_rejects_invalid_kvnr() -> None:
    with pytest.raises(ValueError, match="KVNR"):
        EmpEntryContext(kvnr="X110411318", authored_on=date(2026, 12, 1))


def test_add_emp_entry_parameters_shape() -> None:
    projection = _project(_medication(), CONTEXT)
    parameters = projection.add_emp_entry_parameters(
        "0b383501-f078-464b-b984-9fdb6751601b"
    )
    assert parameters["meta"] == {"profile": [ADD_EMP_ENTRY_PARAMETERS_PROFILE]}
    names = [parameter["name"] for parameter in parameters["parameter"]]
    assert names == ["acknowledgedChronologyId", "medication", "empEntry"]
    assert parameters["parameter"][1]["part"][0]["resource"] == projection.medication
    assert parameters["parameter"][2]["resource"] == projection.medication_request
    # Without acknowledgement the 2..3 parameter cardinality still holds.
    assert len(projection.add_emp_entry_parameters()["parameter"]) == 2


def test_update_emp_entry_parameters_reference_existing_entry() -> None:
    projection = _project(_medication(), CONTEXT)
    parameters = projection.update_emp_entry_parameters(
        medication_plan_identifier="3dfe8327-dd4c-4e53-a695-cd2e0b21e699",
        medication_reference="Medication/13c66845-d0ce-43e1-9b0b-884cbbe8df7f",
    )
    identifier, entry = parameters["parameter"]
    assert identifier["valueIdentifier"]["system"] == EMP_IDENTIFIER_SYSTEM
    request = entry["resource"]
    assert request["identifier"][0]["value"] == "3dfe8327-dd4c-4e53-a695-cd2e0b21e699"
    assert request["medicationReference"] == {
        "reference": "Medication/13c66845-d0ce-43e1-9b0b-884cbbe8df7f"
    }
    # The projection itself stays unchanged.
    assert "identifier" not in projection.medication_request
    with pytest.raises(EpaProjectionError, match="non-versioned"):
        projection.update_emp_entry_parameters(
            medication_plan_identifier="x",
            medication_reference="Medication/1/_history/2",
        )
