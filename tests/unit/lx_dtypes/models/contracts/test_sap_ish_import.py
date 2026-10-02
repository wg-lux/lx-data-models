from datetime import date

import pytest
from pydantic import ValidationError

from lx_dtypes.models.contracts.sap_ish_import import (
    dump_sap_ish_drop_file_payload,
    validate_sap_ish_drop_file_payload,
)


@pytest.mark.parametrize("number", [float("nan"), float("inf"), -float("inf")])
def test_sap_payload_rejects_nonfinite_nested_values(number: float) -> None:
    with pytest.raises(ValidationError):
        validate_sap_ish_drop_file_payload({"rows": [{"value": number}]})


def test_sap_payload_preserves_unicode_identifiers_dates_and_copy_isolation() -> None:
    payload = validate_sap_ish_drop_file_payload(
        {
            "identifier": "00001234567890123456",
            "rows": [{"label": "日本語 – العربية", "date": date(2026, 1, 2)}],
        }
    )
    first = dump_sap_ish_drop_file_payload(payload)
    rows = first["rows"]
    assert isinstance(rows, list)
    rows.clear()
    assert dump_sap_ish_drop_file_payload(payload) == {
        "identifier": "00001234567890123456",
        "rows": [{"label": "日本語 – العربية", "date": date(2026, 1, 2)}],
    }
