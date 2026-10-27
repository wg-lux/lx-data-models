from __future__ import annotations

import pytest
from pydantic import TypeAdapter, ValidationError

from lx_dtypes.models.contracts.german_fhir import (
    Kvnr,
    Pzn,
    is_valid_kvnr,
    is_valid_pzn,
)
from lx_dtypes.models.contracts.kbv_key_tables import (
    BMP_DOSIEREINHEIT,
    KBV_DARREICHUNGSFORM,
)
from lx_dtypes.models.contracts.medication import MedicationEntryFields


@pytest.mark.parametrize(
    "value",
    [
        "X110411319",  # gematik ePA medication IG 1.3.5 test insurant
        "A000000002",
    ],
)
def test_valid_kvnr(value: str) -> None:
    assert is_valid_kvnr(value)
    assert TypeAdapter(Kvnr).validate_python(value) == value


@pytest.mark.parametrize(
    "value", ["X110411318", "x110411319", "X11041131", "1110411319", ""]
)
def test_invalid_kvnr(value: str) -> None:
    assert not is_valid_kvnr(value)
    with pytest.raises(ValidationError):
        TypeAdapter(Kvnr).validate_python(value)


@pytest.mark.parametrize("value", ["04351736", "12345678"])
def test_valid_pzn(value: str) -> None:
    assert is_valid_pzn(value)
    assert TypeAdapter(Pzn).validate_python(value) == value


@pytest.mark.parametrize("value", ["04351737", "1234567", "abcdefgh", "00002000"])
def test_invalid_pzn(value: str) -> None:
    # 00002000: weighted sum 2*5 leaves remainder 10, which is never issued.
    assert not is_valid_pzn(value)


def test_medication_entry_rejects_pzn_with_bad_check_digit() -> None:
    with pytest.raises(ValidationError):
        MedicationEntryFields(pzn="04351737")


def test_kbv_key_tables_match_bmp_unit_code_alphabet() -> None:
    expected = {"#", *"0123456789", *"abcdefghijklmnopqrstuv"}
    assert set(BMP_DOSIEREINHEIT) == expected
    assert BMP_DOSIEREINHEIT["1"] == "Stück"
    assert KBV_DARREICHUNGSFORM["FTA"] == "Filmtabletten"
