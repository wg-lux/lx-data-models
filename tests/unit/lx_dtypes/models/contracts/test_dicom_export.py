from datetime import UTC, datetime
from uuid import UUID

import pytest
from pydantic import ValidationError

from lx_dtypes.models.contracts.dicom_export import DicomExportManifestV2


def _manifest() -> dict[str, object]:
    return {
        "schema_version": 2,
        "export_id": "0d61a22b-31f0-48b9-b68d-a3b675a62cab",
        "created_at": datetime(2026, 7, 17, 12, 0, tzinfo=UTC).isoformat(),
        "source_system": "lx-anonymizer",
        "deidentification": {
            "profile": "DICOM PS3.15 Basic Application Confidentiality Profile",
            "method": "LX deterministic pseudonymization",
            "patient_identity_removed": True,
            "clean_pixel_data": True,
        },
        "validation": {
            "validator_name": "dicom-validator",
            "validator_version": "1.0",
            "status": "passed",
        },
        "study": {
            "study_instance_uid": "2.25.1",
            "patient_pseudonym": "PAT_123",
            "study_date": "2026-07-16",
            "series": [
                {
                    "series_instance_uid": "2.25.2",
                    "modality": "es",
                    "instances": [
                        {
                            "sop_instance_uid": "2.25.3",
                            "sop_class_uid": "1.2.840.10008.5.1.4.1.1.77.1.1.1",
                            "transfer_syntax_uid": "1.2.840.10008.1.2.1",
                            "artifact_reference": "dicom/2.25.3.dcm",
                            "artifact_class": "anonymized_processed",
                            "artifact_sha256": "a" * 64,
                            "size_bytes": 42,
                        }
                    ],
                }
            ],
        },
    }


def test_manifest_v2_normalizes_valid_payload() -> None:
    manifest = DicomExportManifestV2.model_validate(_manifest())

    assert manifest.export_id == UUID("0d61a22b-31f0-48b9-b68d-a3b675a62cab")
    assert manifest.study.series[0].modality == "ES"
    assert manifest.study.series[0].instances[0].artifact_sha256 == "a" * 64


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("study", "study_instance_uid"), "not-a-uid"),
        (
            ("study", "series", 0, "instances", 0, "artifact_sha256"),
            "invalid",
        ),
        (("deidentification", "patient_identity_removed"), False),
        (("validation", "status"), "failed"),
        (
            ("study", "series", 0, "instances", 0, "artifact_class"),
            "raw",
        ),
        (
            ("study", "series", 0, "instances", 0, "artifact_reference"),
            "../raw/instance.dcm",
        ),
    ],
)
def test_manifest_v2_rejects_invalid_invariants(
    path: tuple[str | int, ...], value: object
) -> None:
    payload = _manifest()
    target: object = payload
    for part in path[:-1]:
        target = target[part]  # type: ignore[index]
    target[path[-1]] = value  # type: ignore[index]

    with pytest.raises(ValidationError):
        DicomExportManifestV2.model_validate(payload)


def test_manifest_v2_rejects_duplicate_sop_instance_uid() -> None:
    payload = _manifest()
    study = payload["study"]
    assert isinstance(study, dict)
    series = study["series"]
    assert isinstance(series, list)
    first_series = series[0]
    assert isinstance(first_series, dict)
    instances = first_series["instances"]
    assert isinstance(instances, list)
    duplicate = dict(instances[0])
    instances.append(duplicate)

    with pytest.raises(ValidationError, match="SOP Instance UIDs"):
        DicomExportManifestV2.model_validate(payload)
