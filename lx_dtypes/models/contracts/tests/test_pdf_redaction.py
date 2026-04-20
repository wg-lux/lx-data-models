from __future__ import annotations

import pytest

from lx_dtypes.models.contracts import (
    PdfRedactionRequest,
    PdfRedactionResponse,
    ValidationError,
)


def test_pdf_redaction_request_parses_string_manifest() -> None:
    payload = PdfRedactionRequest.model_validate(
        {
            "source_type": "processed",
            "redaction_manifest": (
                '{"version":1,"normalized":true,"pages":'
                '[{"page":1,"boxes":[{"x":0.1,"y":0.2,"width":0.3,"height":0.4}]}]}'
            ),
            "note": "  reviewed  ",
            "client_source_sha256": "A" * 64,
        }
    )

    assert payload.source_type == "processed"
    assert payload.note == "reviewed"
    assert payload.client_source_sha256 == "a" * 64
    assert payload.redaction_manifest.pages[0].boxes[0].width == 0.3


def test_pdf_redaction_request_rejects_out_of_bounds_box() -> None:
    with pytest.raises(ValidationError):
        PdfRedactionRequest.model_validate(
            {
                "source_type": "raw",
                "redaction_manifest": {
                    "version": 1,
                    "normalized": True,
                    "pages": [
                        {
                            "page": 1,
                            "boxes": [
                                {
                                    "x": 0.9,
                                    "y": 0.1,
                                    "width": 0.2,
                                    "height": 0.2,
                                }
                            ],
                        }
                    ],
                },
            }
        )


def test_pdf_redaction_response_round_trips() -> None:
    payload = PdfRedactionResponse.model_validate(
        {
            "file_id": 1,
            "revision_id": 2,
            "processed_stream_url": "/api/media/pdfs/1/stream/?type=processed",
            "status": "done_processing_anonymization",
            "anonymization_validated": False,
            "updated_at": "2026-03-11T15:00:00+00:00",
        }
    )

    assert payload.file_id == 1
    assert payload.revision_id == 2
    assert payload.anonymization_validated is False
