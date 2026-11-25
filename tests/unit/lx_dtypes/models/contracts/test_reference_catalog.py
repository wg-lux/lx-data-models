from importlib.resources import files
from pathlib import Path

import pytest
from pydantic import ValidationError

from lx_dtypes.knowledge_bases import get_packaged_knowledge_base
from lx_dtypes.models.contracts.knowledge_base import KnowledgeBaseIdentity
from lx_dtypes.models.contracts.reference_catalog import ReferenceCatalogPayload
from lx_dtypes.models.contracts.reference_catalog_snapshot import (
    ReferenceCatalogSnapshot,
)
from lx_dtypes.models.interface.DataLoader import DataLoader


def test_packaged_catalog_roundtrip_in_standard_loader():
    root = get_packaged_knowledge_base(
        "endoreg_reference", "1.0.0"
    ).installed_data_root()
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
    from lx_dtypes.models.contracts.reference_catalog import (
        LabValueReference,
        MedicationReference,
    )

    medications = [
        record for record in payload.records if isinstance(record, MedicationReference)
    ]
    labs = [
        record for record in payload.records if isinstance(record, LabValueReference)
    ]
    assert medications and labs
    assert any(record.name == "apixaban" for record in medications)
    assert any(record.name == "hemoglobin" for record in labs)
    for record in [*medications, *labs]:
        assert type(record).model_validate_json(record.model_dump_json()) == record
    lab_data = labs[0].model_dump()
    for mutation in (
        {"numeric_precision": -1},
        {"bound_adjustment_factor": -0.1},
        {"default_normal_range": {"min": 10.0, "max": 1.0}},
    ):
        with pytest.raises(ValidationError):
            LabValueReference.model_validate({**lab_data, **mutation})


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
    kb = DataLoader(
        input_dirs=[
            root / "terminology" / module,
            get_packaged_knowledge_base(
                "endoreg_reference", "1.0.0"
            ).installed_data_root(),
        ]
    ).load_knowledge_base(module)
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


def test_concrete_catalog_discriminator_is_validated_through_base_interface() -> None:
    from lx_dtypes.models.contracts.reference_catalog import (
        CatalogRecordBase,
        GenderReference,
        ReferenceKind,
    )

    record: CatalogRecordBase = GenderReference.model_validate(
        {"name": "unknown", "abbreviation": None, "description": None}
    )
    assert record.kind is ReferenceKind.GENDER

    invalid: CatalogRecordBase = record.model_copy(update={"record_type": 1})
    with pytest.raises(TypeError, match="discriminator must be a string"):
        _ = invalid.kind
    with pytest.raises(AttributeError):
        _ = CatalogRecordBase().kind


def _packaged_records(input_dir: Path) -> ReferenceCatalogPayload:
    kb = DataLoader(input_dirs=[input_dir]).load_knowledge_base("endoreg_reference")
    return ReferenceCatalogPayload.model_validate(
        {
            "records": [
                record.model_dump(mode="json", by_alias=True)
                for catalog in kb.reference_catalog.values()
                for record in catalog.payload.records
            ]
        }
    )


def test_reference_1_1_0_only_adds_resolved_gender_aliases() -> None:
    from lx_dtypes.models.contracts.reference_catalog import (
        GenderAliasReference,
        ReferenceKind,
    )

    root = Path(str(files("lx_dtypes").joinpath("data")))
    released = _packaged_records(
        get_packaged_knowledge_base("endoreg_reference", "1.0.0").installed_data_root()
    )
    current = _packaged_records(root / "terminology/versions/endoreg_reference/1.1.0")
    added = [record for record in current.records if record not in released.records]
    assert all(record in current.records for record in released.records)
    assert added and all(isinstance(record, GenderAliasReference) for record in added)
    identity = KnowledgeBaseIdentity(
        knowledge_base_module="endoreg_reference", knowledge_base_version="1.1.0"
    )
    # Construction rejects aliases whose gender is absent from the snapshot.
    ReferenceCatalogSnapshot(
        identity=identity,
        payload=current,
        snapshot_id=ReferenceCatalogSnapshot.content_digest(identity, current),
    )
    targets = {
        record.name: record.gender.name
        for record in added
        if isinstance(record, GenderAliasReference)
    }
    assert targets["weiblich"] == "female"
    assert targets["männlich"] == "male"
    assert {targets[name] for name in ("d", "divers", "diverse")} == {"other"}
    genders = {
        record.key[1]
        for record in current.records
        if record.kind is ReferenceKind.GENDER
    }
    assert not genders & set(targets)


@pytest.mark.parametrize(
    "spelling, normalized",
    [
        ("W", "w"),
        ("  Weiblich ", "weiblich"),
        ("MÄNNLICH", "männlich"),
        ("not  given", "not given"),
    ],
)
def test_gender_spelling_normalization(spelling: str, normalized: str) -> None:
    from lx_dtypes.models.contracts.reference_catalog import normalize_gender_spelling

    assert normalize_gender_spelling(spelling) == normalized


@pytest.mark.parametrize("name", ["W", " w", "weib  lich", "", "x" * 256])
def test_gender_alias_rejects_unnormalized_or_invalid_names(name: str) -> None:
    with pytest.raises(ValidationError):
        ReferenceCatalogPayload.model_validate(
            {
                "records": [
                    {
                        "record_type": "gender_alias",
                        "name": name,
                        "gender": {"name": "female"},
                    }
                ]
            }
        )


def test_gender_alias_requires_gender_in_snapshot() -> None:
    payload = ReferenceCatalogPayload.model_validate(
        {
            "records": [
                {
                    "record_type": "gender_alias",
                    "name": "w",
                    "gender": {"name": "female"},
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


def test_dependency_catalog_snapshot_is_closed_and_pins_source_dates() -> None:
    from lx_dtypes.models.contracts.adapters import record_to_core_concept
    from lx_dtypes.models.contracts.package_snapshot import build_package_snapshot

    root = Path(str(files("lx_dtypes").joinpath("data")))
    kb = DataLoader(input_dirs=[root]).load_knowledge_base("endoreg_reference")
    payload = _packaged_records(root)
    identity = KnowledgeBaseIdentity(
        knowledge_base_module="endoreg_reference", knowledge_base_version="2.0.0"
    )
    package = build_package_snapshot(kb)
    reloaded_package = build_package_snapshot(
        DataLoader(input_dirs=[root]).load_knowledge_base("endoreg_reference")
    )
    assert ReferenceCatalogSnapshot.content_digest(
        identity, payload, clinical_package=package
    ) == ReferenceCatalogSnapshot.content_digest(
        identity, payload, clinical_package=reloaded_package
    )
    snapshot = ReferenceCatalogSnapshot(
        identity=identity,
        payload=payload,
        clinical_package=package,
        snapshot_id=ReferenceCatalogSnapshot.content_digest(
            identity, payload, clinical_package=package
        ),
    )
    assert ReferenceCatalogSnapshot.model_validate_json(
        snapshot.model_dump_json()
    ).model_dump(mode="json") == snapshot.model_dump(mode="json")
    with pytest.raises(ValidationError, match="Unresolved reference"):
        ReferenceCatalogSnapshot(
            identity=identity,
            payload=payload,
            snapshot_id=ReferenceCatalogSnapshot.content_digest(identity, payload),
        )
    raw = snapshot.model_dump(mode="json")
    raw["clinical_package"] = None
    with pytest.raises(ValidationError, match="digest mismatch"):
        ReferenceCatalogSnapshot.model_validate(raw)
    source = kb.information_source["guideline_quality_in_gi"]
    assert (
        record_to_core_concept("information_source", source).model_dump()["date"]
        == "2025-01-01"
    )
    assert (
        "date"
        not in record_to_core_concept(
            "information_source", kb.information_source["unknown"]
        ).model_dump()
    )
