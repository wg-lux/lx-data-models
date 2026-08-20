import pytest
from pydantic import ValidationError

from lx_dtypes.models.contracts.terminology_catalog import (
    ExaminationCatalogDTO,
    IndicationCatalogDTO,
)


def test_examination_catalog_dto_preserves_localized_names() -> None:
    dto = ExaminationCatalogDTO.model_validate(
        {
            "id": 1,
            "name": "colonoscopy",
            "name_de": "Koloskopie",
            "name_en": "Colonoscopy",
            "findings": [],
            "examination_types": [],
        }
    )

    assert dto.model_dump(mode="json")["name_de"] == "Koloskopie"
    assert dto.model_dump(mode="json")["name_en"] == "Colonoscopy"


def test_indication_catalog_dto_guarantees_upstream_fallbacks() -> None:
    dto = IndicationCatalogDTO.model_validate({"id": 2, "name": "screening"})

    assert dto.name_de == "screening"
    assert dto.name_en == "screening"


def test_catalog_dto_rejects_unknown_transport_fields() -> None:
    with pytest.raises(ValidationError, match="extra_forbidden"):
        IndicationCatalogDTO.model_validate(
            {"id": 2, "name": "screening", "displayName": "simulated"}
        )
