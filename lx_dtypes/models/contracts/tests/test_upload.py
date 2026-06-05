from __future__ import annotations

import pytest
from pydantic import ValidationError

from lx_dtypes.models.contracts.upload import (
    UploadApiRequestPayload,
    upload_api_request_data_from_mapping,
    validate_upload_api_request_payload,
)


def test_upload_api_request_payload_defaults_to_empty_scope() -> None:
    payload = validate_upload_api_request_payload({})

    assert payload == UploadApiRequestPayload(
        center_key="",
        center_name="",
        source_system="api",
        idempotency_key="",
    )


def test_upload_api_request_payload_strips_form_values() -> None:
    payload = validate_upload_api_request_payload(
        {
            "center_key": "  ukw  ",
            "center_name": "  University Hospital  ",
            "source_system": "  lx-annotate  ",
            "idempotency_key": "  request-1  ",
        }
    )

    assert payload.center_key == "ukw"
    assert payload.center_name == "University Hospital"
    assert payload.source_system == "lx-annotate"
    assert payload.idempotency_key == "request-1"


def test_upload_api_request_payload_defaults_blank_source_system() -> None:
    payload = validate_upload_api_request_payload({"source_system": "  "})

    assert payload.source_system == "api"


def test_upload_api_request_data_excludes_multipart_file_field() -> None:
    data = upload_api_request_data_from_mapping(
        {
            "center_key": "site-a",
            "file": "not-part-of-the-contract",
        }
    )

    assert data == {"center_key": "site-a"}


def test_upload_api_request_payload_rejects_unknown_contract_fields() -> None:
    with pytest.raises(ValidationError):
        UploadApiRequestPayload.model_validate({"unexpected": "field"})
