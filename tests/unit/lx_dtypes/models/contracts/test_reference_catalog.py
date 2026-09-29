from importlib.resources import files
from pathlib import Path

import pytest
from pydantic import ValidationError

from lx_dtypes.models.contracts.knowledge_base import KnowledgeBaseIdentity
from lx_dtypes.models.contracts.reference_catalog import ReferenceCatalogPayload
from lx_dtypes.models.contracts.reference_catalog_snapshot import (
    ReferenceCatalogSnapshot,
)
from lx_dtypes.models.interface.DataLoader import DataLoader


def test_packaged_catalog_roundtrip_in_standard_loader():
    root = Path(str(files("lx_dtypes").joinpath("data")))
    kb = DataLoader(input_dirs=[root]).load_knowledge_base("endoreg_reference")
    records = [
        record.model_dump(mode="json", by_alias=True)
        for catalog in kb.reference_catalog.values()
        for record in catalog.payload.records
    ]
    payload = ReferenceCatalogPayload.model_validate({"records": records})
    identity = KnowledgeBaseIdentity(
        knowledge_base_module="endoreg_reference", knowledge_base_version="1.0.0"
    )
    snapshot = ReferenceCatalogSnapshot(
        identity=identity,
        payload=payload,
        snapshot_id=ReferenceCatalogSnapshot.content_digest(identity, payload),
    )
    assert len(payload.records) == 673
    assert (
        ReferenceCatalogSnapshot.model_validate_json(
            snapshot.model_dump_json(by_alias=True)
        )
        == snapshot
    )
    assert len(kb.export_record_lists()["reference_catalogs"]) == 50


@pytest.mark.parametrize(
    "mutation",
    [
        {"unknown": True},
        {"name": ""},
        {"description": 12},
        {"record_type": "patient"},
    ],
)
def test_catalog_rejects_unknown_or_invalid_definitions(mutation):
    record = {
        "record_type": "contraindication",
        "name": "clinical_condition",
        "description": None,
    }
    record.update(mutation)
    with pytest.raises(ValidationError):
        ReferenceCatalogPayload.model_validate({"records": [record]})


def test_catalog_rejects_duplicates_and_dangling_relations():
    record = {
        "record_type": "contraindication",
        "name": "clinical_condition",
        "description": None,
    }
    with pytest.raises(ValidationError, match="duplicate identities"):
        ReferenceCatalogPayload.model_validate({"records": [record, record]})
    payload = ReferenceCatalogPayload.model_validate(
        {
            "records": [
                {
                    "record_type": "disease_classification",
                    "name": "grading",
                    "disease": {"name": "missing"},
                }
            ]
        }
    )
    identity = KnowledgeBaseIdentity(
        knowledge_base_module="clinical", knowledge_base_version="1.0.0"
    )
    with pytest.raises(ValidationError, match="Unresolved reference"):
        ReferenceCatalogSnapshot(
            identity=identity,
            payload=payload,
            snapshot_id=ReferenceCatalogSnapshot.content_digest(identity, payload),
        )


@pytest.mark.parametrize(
    "module, count", [("endoreg_workforce", 39), ("endoreg_green_endoscopy", 826)]
)
def test_optional_packages_have_closed_reference_graphs(
    module: str, count: int
) -> None:
    root = Path(str(files("lx_dtypes").joinpath("data")))
    kb = DataLoader(input_dirs=[root]).load_knowledge_base(module)
    payload = ReferenceCatalogPayload.model_validate(
        {
            "records": [
                record.model_dump(mode="json", by_alias=True)
                for catalog in kb.reference_catalog.values()
                for record in catalog.payload.records
            ]
        }
    )
    identity = KnowledgeBaseIdentity(
        knowledge_base_module=module, knowledge_base_version="1.0.0"
    )
    snapshot = ReferenceCatalogSnapshot(
        identity=identity,
        payload=payload,
        snapshot_id=ReferenceCatalogSnapshot.content_digest(identity, payload),
    )
    assert len(snapshot.payload.records) == count
    assert (
        ReferenceCatalogSnapshot.model_validate_json(
            snapshot.model_dump_json(by_alias=True)
        )
        == snapshot
    )


def test_composite_identity_uses_all_declared_natural_keys() -> None:
    from lx_dtypes.models.contracts.reference_catalog import CenterWasteReference

    first = CenterWasteReference.model_validate(
        {
            "center": {"name": "site"},
            "waste": {"name": "paper"},
            "year": 2025,
            "quantity": 12.0,
            "unit": {"name": "kg"},
            "emission_factor": None,
        }
    )
    # Quantity is mutable meaning, never part of identity; year is identity.
    assert first.key == first.model_copy(update={"quantity": 13.0}).key
    assert first.key != first.model_copy(update={"year": 2026}).key
    assert first.key != first.model_copy(update={"waste": first.center}).key
