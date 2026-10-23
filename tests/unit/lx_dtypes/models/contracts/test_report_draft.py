from __future__ import annotations

import math

import pytest
from pydantic import ValidationError

from lx_dtypes.models.contracts.report_draft import (
    PatientExaminationReportDraft,
    dump_patient_examination_report_draft,
)


@pytest.mark.parametrize(
    "template_identity",
    [
        {
            "module_name": "report_template_examples",
            "knowledge_base_version": "0.2.8",
            "template_version": "3",
            "template_hash": "sha256:template",
            "lifecycle_status": "published",
        },
        {
            "moduleName": "report_template_examples",
            "knowledgeBaseVersion": "0.2.8",
            "templateVersion": "3",
            "templateHash": "sha256:template",
            "lifecycleStatus": "published",
        },
    ],
)
def test_report_draft_roundtrip_uses_canonical_snake_case(
    template_identity: dict[str, object],
) -> None:
    result = dump_patient_examination_report_draft(
        {
            "module_name": " report_template_examples ",
            "template_name": " colonoscopy ",
            "template_identity": template_identity,
            "indications": [
                {"examination_indication_id": 12, "indication_choice_id": 21}
            ],
            "template_section_drafts": {
                "findings": {
                    "note": "No acute bleeding",
                    "include_patient_data": True,
                    "include_examination_data": False,
                }
            },
            "selected_report_language": "de",
            "active_report_id": 88,
            "report_text_mode": "manual",
            "rendered_text": "Klinischer Freitext",
            "payload": {"examination": "colonoscopy", "patientFindings": []},
        }
    )

    assert result == {
        "schema_version": "1.0",
        "revision": 0,
        "module_name": "report_template_examples",
        "template_name": "colonoscopy",
        "template_identity": {
            "module_name": "report_template_examples",
            "knowledge_base_version": "0.2.8",
            "template_version": "3",
            "template_hash": "sha256:template",
            "lifecycle_status": "published",
        },
        "indications": [{"examination_indication_id": 12, "indication_choice_id": 21}],
        "template_section_drafts": {
            "findings": {
                "note": "No acute bleeding",
                "include_patient_data": True,
                "include_examination_data": False,
            }
        },
        "selected_report_language": "de",
        "active_report_id": 88,
        "report_text_mode": "manual",
        "rendered_text": "Klinischer Freitext",
        "payload": {"examination": "colonoscopy", "patientFindings": []},
    }


@pytest.mark.parametrize(
    "value",
    [
        {"schema_version": "2.0", "payload": {}},
        {"payload": {}, "unexpected": True},
        {"payload": []},
        {"payload": {"answer": math.nan}},
        {"payload": {"answer": math.inf}},
        {"module_name": 7, "payload": {}},
        {"report_text_mode": "unknown", "payload": {}},
        {"selected_report_language": "fr", "payload": {}},
        {"active_report_id": 0, "payload": {}},
        {"revision": -1, "payload": {}},
        {"revision": 1.5, "payload": {}},
        {"template_section_drafts": {"findings": {"note": 7}}, "payload": {}},
    ],
)
def test_report_draft_rejects_noncanonical_persisted_values(
    value: dict[str, object],
) -> None:
    with pytest.raises(ValidationError):
        PatientExaminationReportDraft.model_validate(value)


def test_report_draft_empty_sentinel_remains_empty() -> None:
    assert dump_patient_examination_report_draft(None) == {}
    assert dump_patient_examination_report_draft({}) == {}
