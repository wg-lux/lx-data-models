import math

import pytest
from pydantic import BaseModel, ValidationError

from lx_dtypes.models import SensitiveMeta as ExportedSensitiveMeta
from lx_dtypes.models import SensitiveMetaDataDict
from lx_dtypes.models import SensitiveMetaState
from lx_dtypes.models import SensitiveMetaStateDataDict
from lx_dtypes.models.meta.SensitiveMeta import SensitiveMeta


def test_sensitive_meta_is_exported_from_models_namespace() -> None:
    assert ExportedSensitiveMeta is SensitiveMeta
    assert SensitiveMetaDataDict.__name__ == "SensitiveMetaDataDict"
    assert SensitiveMetaState.__name__ == "SensitiveMetaState"
    assert SensitiveMetaStateDataDict.__name__ == "SensitiveMetaStateDataDict"


def test_sensitive_meta_normalizes_legacy_input_to_lx_dtypes_fields() -> None:
    meta = SensitiveMeta.model_validate(
        {
            "patient_first_name": "  Max  ",
            "patient_last_name": "Muster",
            "patient_dob": "02.01.1990",
            "patient_gender_name": "male",
            "examiner_last_name": "Arzt",
            "unknown_field": "ignored",
        }
    )

    dumped = meta.model_dump()
    assert meta.first_name == "Max"
    assert meta.last_name == "Muster"
    assert meta.dob is not None
    assert meta.dob.isoformat() == "1990-01-02"
    assert meta.gender == "male"
    assert meta.examiner_last_name == "Arzt"
    assert "patient_first_name" not in dumped
    assert "patient_last_name" not in dumped
    assert "patient_dob" not in dumped
    assert "patient_gender_name" not in dumped


def test_safe_update_accepts_mapping_kwargs_and_base_model() -> None:
    class Dummy(BaseModel):
        patient_dob: str | None = None

    meta = SensitiveMeta(first_name="Alice")
    meta.safe_update({"patient_last_name": "Smith"})
    meta.safe_update(gender="female")
    meta.safe_update(Dummy(patient_dob="1990-01-01"))

    assert meta.first_name == "Alice"
    assert meta.last_name == "Smith"
    assert meta.gender == "female"
    assert meta.dob is not None
    assert meta.dob.isoformat() == "1990-01-01"


def test_safe_update_is_fill_only_and_normalizes_blanks() -> None:
    meta = SensitiveMeta(first_name="Alice", last_name="Smith")
    meta.safe_update(first_name="Bob", last_name=" ", casenumber="E123")

    assert meta.first_name == "Alice"
    assert meta.last_name == "Smith"
    assert meta.casenumber == "E123"


def test_safe_update_prevents_partial_mutation_on_validation_error() -> None:
    meta = SensitiveMeta(first_name="Alice", casenumber="E123")
    meta.safe_update({"last_name": "Smith", "dob": ["bad"]})

    assert meta.first_name == "Alice"
    assert meta.last_name == "unknown"
    assert meta.casenumber == "E123"
    assert meta.dob is None


def test_null_equivalent_values_are_normalized() -> None:
    meta = SensitiveMeta(
        first_name="unknown",
        last_name=" ",
        casenumber="n/a",
        examination_time=math.nan,
        text=[],
    )

    assert meta.first_name == "unknown"
    assert meta.last_name == "unknown"
    assert meta.casenumber is None
    assert meta.examination_time is None
    assert meta.text is None


def test_unknown_fields_are_ignored_during_contract_normalization() -> None:
    meta = SensitiveMeta.model_validate({"first_name": "Max", "extra": "ignored"})
    assert meta.first_name == "Max"

    with pytest.raises(ValidationError):
        SensitiveMetaState.model_validate(
            {"sensitive_meta": "abc", "extra": "still-forbidden"}
        )
