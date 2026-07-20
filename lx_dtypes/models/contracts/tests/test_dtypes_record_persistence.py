from __future__ import annotations

import pytest
from pydantic import ValidationError

from lx_dtypes.models.contracts import (
    DtypesRecordPersistencePayload,
    dump_dtypes_record_persistence_payload,
    parse_dtypes_record_persistence_payload,
)
from lx_dtypes.models.contracts.json_types import JsonValue


def _complete_record() -> dict[str, JsonValue]:
    return {
        "patient": "patient-7",
        "examiners": ["examiner-2"],
        "examination": "colonoscopy",
        "knowledge_base_module": "report_template_examples",
        "knowledge_base_version": "0.1.0",
        "patient_findings": [
            {
                "finding": "colon_polyp",
                "patient_examination": "42",
                "patient_finding_classifications": [
                    {
                        "patient_finding": "finding-1",
                        "patient_finding_classification_choices": [
                            {
                                "classification": "lesion_size_mm",
                                "classification_choice": "lesion_size_oval_mm",
                                "patient_finding_classifications": "group-1",
                            }
                        ],
                    }
                ],
                "patient_finding_interventions": [
                    {
                        "patient_finding": "finding-1",
                        "patient_finding_interventions": [
                            {
                                "patient_finding_interventions": "group-2",
                                "intervention": "biopsy",
                            }
                        ],
                    }
                ],
            }
        ],
        "patient_indications": [
            {
                "indication": "screening",
                "patient_examination": "42",
                "patient_indication_classifications": [
                    {
                        "classification": "screening_program",
                        "classification_choice": "organized",
                        "patient_indication": "indication-1",
                        "patient_indication_classification_descriptors": [
                            {
                                "descriptor_value": True,
                                "classification_choice_descriptor": "eligible",
                                "patient_indication_classification": "group-3",
                            }
                        ],
                    }
                ],
            }
        ],
    }


def _json_object(value: JsonValue) -> dict[str, JsonValue]:
    assert isinstance(value, dict)
    return value


def _json_list(payload: dict[str, JsonValue], key: str) -> list[JsonValue]:
    value = payload[key]
    assert isinstance(value, list)
    return value


def test_complete_record_round_trips_through_public_contract() -> None:
    record = parse_dtypes_record_persistence_payload(_complete_record())

    assert isinstance(record, DtypesRecordPersistencePayload)
    assert record.patient_findings[0].patient_examination == "42"
    assert (
        record.patient_findings[0]
        .patient_finding_classifications[0]
        .patient_finding_classification_choices[0]
        .classification_choice
        == "lesion_size_oval_mm"
    )
    assert (
        record.patient_indications[0]
        .patient_indication_classifications[0]
        .patient_indication_classification_descriptors[0]
        .descriptor_value
        is True
    )

    dumped = dump_dtypes_record_persistence_payload(record)
    assert parse_dtypes_record_persistence_payload(dumped) == record


@pytest.mark.parametrize(
    "path",
    ["root", "finding", "classification_choice"],
)
def test_record_contract_rejects_unknown_fields_at_every_level(path: str) -> None:
    payload = _complete_record()
    if path == "root":
        payload["unexpected"] = True
    elif path == "finding":
        finding = _json_object(_json_list(payload, "patient_findings")[0])
        finding["unexpected"] = True
    else:
        finding = _json_object(_json_list(payload, "patient_findings")[0])
        group = _json_object(_json_list(finding, "patient_finding_classifications")[0])
        choice = _json_object(
            _json_list(group, "patient_finding_classification_choices")[0]
        )
        choice["unexpected"] = True

    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        parse_dtypes_record_persistence_payload(payload)
