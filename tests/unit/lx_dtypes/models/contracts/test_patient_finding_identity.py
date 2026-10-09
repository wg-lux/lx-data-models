from uuid import uuid4

import pytest
from pydantic import ValidationError

from lx_dtypes.models.contracts.patient_examination_report import (
    SegmentFrameSelectorPatchPayload,
    dump_selector_patch_payload,
)
from lx_dtypes.models.contracts.patient_finding import PatientFindingIdentityPayload


def test_finding_identity_accepts_uuid_transport_and_local_primary_key() -> None:
    identity = uuid4()
    parsed = PatientFindingIdentityPayload.model_validate(
        {"instance_id": str(identity), "patient_finding_id": 12}
    )
    assert parsed.instance_id == identity
    assert parsed.patient_finding_id == 12


@pytest.mark.parametrize("value", [True, 0, -1, 1.5, "12"])
def test_finding_primary_keys_are_strict_positive_integers(value: object) -> None:
    with pytest.raises(ValidationError):
        PatientFindingIdentityPayload.model_validate({"patient_finding_id": value})
    with pytest.raises(ValidationError):
        SegmentFrameSelectorPatchPayload.model_validate(
            {
                "patient_examination_id": 1,
                "segment_id": 2,
                "patient_finding_id": value,
            }
        )


@pytest.mark.parametrize("value", ["", "not-a-uuid", True, 42])
def test_invalid_instance_uuid_is_rejected(value: object) -> None:
    with pytest.raises(ValidationError):
        PatientFindingIdentityPayload.model_validate({"instance_id": value})


def test_selector_preserves_explicit_finding_identity() -> None:
    parsed = SegmentFrameSelectorPatchPayload.model_validate(
        {
            "patient_examination_id": 1,
            "segment_id": 2,
            "patient_finding_id": 3,
        }
    )
    assert dump_selector_patch_payload(parsed).get("patient_finding_id") == 3
