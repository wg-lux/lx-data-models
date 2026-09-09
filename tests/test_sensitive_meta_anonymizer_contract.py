import math
from datetime import date
from typing import Any, cast

import pytest
from pydantic import BaseModel, ValidationError

from lx_dtypes.models import SensitiveMeta as ExportedSensitiveMeta
from lx_dtypes.models import (
    SensitiveMetaDataDict,
    SensitiveMetaState,
    SensitiveMetaStateDataDict,
)
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


def test_safe_update_projects_known_fields_from_mixed_payload() -> None:
    meta = SensitiveMeta()

    meta.safe_update(
        {
            "backend": "rapidocr",
            "roi_count": 5,
            "patient_first_name": "Thomas",
        }
    )

    assert meta.first_name == "Thomas"


def test_null_equivalent_values_are_normalized() -> None:
    meta = SensitiveMeta(
        first_name="unknown",
        last_name=" ",
        casenumber="n/a",
        examination_time=cast(Any, math.nan),
        text=cast(Any, []),
    )

    assert meta.first_name == "unknown"
    assert meta.last_name == "unknown"
    assert meta.casenumber is None
    assert meta.examination_time is None
    assert meta.text is None


def test_unknown_fields_are_rejected_during_contract_normalization() -> None:
    with pytest.raises(ValidationError, match="extra"):
        SensitiveMeta.model_validate({"first_name": "Max", "extra": "rejected"})

    with pytest.raises(ValidationError):
        SensitiveMetaState.model_validate(
            {"sensitive_meta": "abc", "extra": "still-forbidden"}
        )


def test_sensitive_meta_projects_known_fields_from_mixed_boundary_payload() -> None:
    meta = SensitiveMeta.from_mixed_mapping(
        {
            "backend": "rapidocr",
            "roi_count": 5,
            "patient_first_name": " Thomas ",
            "examination_date": "15.02.2024",
        }
    )

    assert meta.first_name == "Thomas"
    assert meta.examination_date == date(2024, 2, 15)
    assert "backend" not in meta.model_dump()


def test_sensitive_meta_mixed_boundary_rejects_invalid_known_field() -> None:
    with pytest.raises(ValidationError, match="dob"):
        SensitiveMeta.from_mixed_mapping(
            {
                "backend": "rapidocr",
                "dob": ["invalid"],
            }
        )


def test_inverted_clinical_dates_are_rejected() -> None:
    with pytest.raises(
        ValidationError,
        match="examination_date must not be earlier than dob",
    ):
        SensitiveMeta.model_validate(
            {
                "first_name": "Max",
                "dob": "2020-01-01",
                "examination_date": "2010-01-01",
            }
        )
