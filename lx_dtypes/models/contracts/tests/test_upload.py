from __future__ import annotations

import pytest
from pydantic import ValidationError
from typing import cast

from lx_dtypes.models.contracts.upload import (
    UploadApiRequestPayload,
    upload_api_request_data_from_mapping,
    validate_upload_api_request_payload,
)
from lx_dtypes.models.contracts.json_types import JsonValue


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


@pytest.mark.parametrize(
    ("field_name", "field_value"),
    [
        ("center_key", cast(JsonValue, {"name": "site-a"})),
        ("center_name", cast(JsonValue, ["University Hospital"])),
        ("source_system", cast(JsonValue, {"system": "lx-annotate"})),
        ("idempotency_key", cast(JsonValue, ["request-1"])),
    ],
)
def test_upload_api_request_payload_rejects_non_string_values(
    field_name: str,
    field_value: JsonValue,
) -> None:
    with pytest.raises(ValueError, match=f"{field_name} must be a string"):
        validate_upload_api_request_payload(
            cast(dict[str, JsonValue], {field_name: field_value})
        )


def test_upload_api_request_data_excludes_multipart_file_field() -> None:
    data = upload_api_request_data_from_mapping(
        {
            "center_key": "site-a",
            "file": "not-part-of-the-contract",
        }
    )

    assert data == {"center_key": "site-a"}


@pytest.mark.parametrize(
    "unknown_field_name",
    ["unexpected", "files", "upload"],
)
def test_upload_api_request_data_rejects_unknown_multipart_fields(
    unknown_field_name: str,
) -> None:
    with pytest.raises(
        ValueError,
        match=rf"Unknown upload request field\(s\): {unknown_field_name}",
    ):
        upload_api_request_data_from_mapping(
            {
                "center_key": "site-a",
                "file": "transport-only",
                unknown_field_name: "not-part-of-the-contract",
            }
        )


def test_upload_api_request_payload_rejects_unknown_field_before_projection() -> None:
    with pytest.raises(ValueError, match="Unknown upload request field"):
        validate_upload_api_request_payload(
            {
                "center_name": "University Hospital",
                "unexpected": "field",
            }
        )


def test_upload_api_request_payload_rejects_unknown_contract_fields() -> None:
    with pytest.raises(ValidationError):
        UploadApiRequestPayload.model_validate({"unexpected": "field"})
