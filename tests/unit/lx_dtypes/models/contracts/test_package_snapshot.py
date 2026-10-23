from importlib.resources import files
from pathlib import Path

import pytest
from pydantic import BaseModel, ValidationError

from lx_dtypes.models.contracts.package_snapshot import (
    PackageSnapshot,
    build_package_snapshot,
    restore_package_snapshot,
)
from lx_dtypes.models.contracts.reference_catalog import (
    ReferenceCatalogPayload,
    WasteReference,
)
from lx_dtypes.models.interface.DataLoader import DataLoader
from lx_dtypes.models.interface.KnowledgeBase import KnowledgeBase
from lx_dtypes.models.knowledge_base.pydantic_main import (
    KB_MODEL_NAMES_ORDERED,
    knowledge_base_models_lookup,
)
from lx_dtypes.packages import load_package
from lx_dtypes.utils.parser import camel_to_snake


def _complete_kb() -> KnowledgeBase:
    extras: dict[str, dict[str, object]] = {
        "ClassificationChoiceDescriptor": {"numeric_min": 0.0, "numeric_max": 1.0},
        "CenterEmployeeList": {
            "examiners": [
                {"center": "synthetic", "first_name": "Test", "last_name": "User"}
            ],
        },
        "ReferenceCatalog": {
            "payload": ReferenceCatalogPayload(
                records=[WasteReference(name="synthetic")]
            ),
        },
        "Citation": {"citation_key": "synthetic", "title": "Synthetic citation"},
        "ReportFinding": {"finding": "Finding"},
        "ReportTemplate": {"examination": "Examination"},
    }
    payload: dict[str, object] = {"config": {"name": "synthetic", "version": "1.0.0"}}
    for kind in KB_MODEL_NAMES_ORDERED:
        model = knowledge_base_models_lookup[kind]
        assert isinstance(model, type) and issubclass(model, BaseModel)
        record = model.model_validate(
            {
                "name": kind,
                "kb_module_name": "synthetic",
                **extras.get(kind, {}),
            }
        )
        payload[camel_to_snake(kind)] = {kind: record}
    return KnowledgeBase.model_validate(payload)


def test_all_registered_families_roundtrip_in_owning_types() -> None:
    kb = _complete_kb()
    snapshot = build_package_snapshot(kb)
    restored = restore_package_snapshot(
        PackageSnapshot.model_validate_json(snapshot.model_dump_json())
    )
    assert set(snapshot.records) == set(KB_MODEL_NAMES_ORDERED)
    for kind in KB_MODEL_NAMES_ORDERED:
        original = getattr(kb, camel_to_snake(kind))[kind]
        recovered = getattr(restored, camel_to_snake(kind))[kind]
        assert type(recovered) is type(original)
        assert recovered.model_dump() == original.model_dump()
    assert build_package_snapshot(restored).snapshot_id == snapshot.snapshot_id


def test_dependency_versions_and_stable_portable_digest() -> None:
    manifest = Path("docs/examples/dtypes_packages/training_preset/config.yaml")
    first = build_package_snapshot(load_package(manifest))
    second = build_package_snapshot(load_package(manifest))
    assert first.snapshot_id == second.snapshot_id
    assert set(first.module_configs) == {"training_preset", "training_terminology"}
    assert all(config.version == "1.0.0" for config in first.module_configs.values())
    assert str(Path.cwd()) not in first.model_dump_json()
    assert (
        build_package_snapshot(restore_package_snapshot(first)).snapshot_id
        == first.snapshot_id
    )


def test_legacy_empty_study_metadata_retains_snapshot_identity() -> None:
    snapshot = build_package_snapshot(_complete_kb())
    legacy = snapshot.model_dump(mode="json")
    del legacy["records"]["StudyPreset"][0]["study_metadata"]["analysis_definitions"]
    restored = restore_package_snapshot(PackageSnapshot.model_validate(legacy))
    assert build_package_snapshot(restored).snapshot_id == snapshot.snapshot_id


@pytest.mark.parametrize(
    "change", ["missing_family", "unknown_family", "invalid_record", "changed_record"]
)
def test_rejects_incomplete_or_changed_persisted_content(change: str) -> None:
    snapshot = build_package_snapshot(_complete_kb())
    payload = snapshot.model_dump(mode="json")
    if change == "missing_family":
        del payload["records"]["StudyPreset"]
    elif change == "unknown_family":
        payload["records"]["Unregistered"] = []
    elif change == "invalid_record":
        payload["records"]["Examination"][0]["not_a_field"] = True
    else:
        payload["records"]["Examination"][0]["description"] = "Changed"
    with pytest.raises(ValidationError):
        PackageSnapshot.model_validate(payload)


def test_rejects_dangling_graph_and_missing_dependency_provenance() -> None:
    kb = _complete_kb()
    kb.examination["Examination"].findings = ["missing"]
    with pytest.raises(ValidationError):
        build_package_snapshot(kb)
    kb = _complete_kb()
    kb.config.modules = ["missing"]
    with pytest.raises(ValidationError, match="exact configs"):
        build_package_snapshot(kb)


def test_content_digest_includes_reference_catalog_semantics() -> None:
    kb = _complete_kb()
    first = build_package_snapshot(kb)
    catalog = kb.reference_catalog["ReferenceCatalog"]
    record = catalog.payload.records[0]
    assert isinstance(record, WasteReference)
    record.name = "different"
    assert build_package_snapshot(kb).snapshot_id != first.snapshot_id


def test_published_template_reuses_readiness_and_retains_draft_state() -> None:
    kb = _complete_kb()
    kb.report_template["ReportTemplate"].examination = "missing"
    with pytest.raises(ValidationError, match="not publishable"):
        build_package_snapshot(kb)
    kb.report_template_lifecycle_status["ReportTemplate"] = "draft"
    restored = restore_package_snapshot(build_package_snapshot(kb))
    assert restored.get_report_template_lifecycle_status("ReportTemplate") == "draft"


def test_coloreg_package_preserves_aliased_reference_metadata() -> None:
    root = Path(str(files("lx_dtypes").joinpath("data")))
    kb = DataLoader(input_dirs=[root]).load_knowledge_base("coloreg")
    snapshot = build_package_snapshot(kb)
    restored = restore_package_snapshot(snapshot)
    assert build_package_snapshot(restored).snapshot_id == snapshot.snapshot_id
    assert restored.reference_catalog.keys() == kb.reference_catalog.keys()
    conditional = {
        name: record.query.model_dump(mode="json")
        for name, record in kb.findings_validator.items()
        if record.query.condition is not None
    }
    assert conditional
    assert {
        name: restored.findings_validator[name].query.model_dump(mode="json")
        for name in conditional
    } == conditional


@pytest.mark.parametrize(
    "module,version",
    [
        ("coloreg", "0.3.0"),
        ("dgvs_reporting", "0.1.0"),
        ("mst_3_0", "3.0.0"),
        ("report_template_examples", "0.1.1"),
        ("star_upper_gi", "0.1.2"),
    ],
)
def test_reporting_snapshots_preserve_strict_guideline_dates(
    module: str, version: str
) -> None:
    root = Path(str(files("lx_dtypes").joinpath("data")))
    kb = DataLoader(input_dirs=[root]).load_knowledge_base(module)
    assert kb.config.version == version
    snapshot = build_package_snapshot(kb)
    roundtrip = PackageSnapshot.model_validate_json(snapshot.model_dump_json())
    restored = restore_package_snapshot(roundtrip)
    references = [
        reference
        for name in sorted(kb.report_template)
        for reference in kb.report_template[name].guideline_references
    ]
    if module == "dgvs_reporting":
        assert references
    assert [
        reference
        for name in sorted(restored.report_template)
        for reference in restored.report_template[name].guideline_references
    ] == references
    assert build_package_snapshot(restored).snapshot_id == snapshot.snapshot_id


def test_report_template_json_date_boundary_remains_strict_for_python() -> None:
    import json

    from lx_dtypes.models.knowledge_base.report_template.ReportTemplate import (
        ReportTemplate,
    )

    payload = {
        "name": "synthetic",
        "examination": "synthetic",
        "guideline_references": [
            {
                "guideline_id": "synthetic",
                "title": "Synthetic",
                "issuing_organization": "Synthetic",
                "version": "1.0",
                "publication_date": "2025-07-01",
                "canonical_url": "https://example.invalid/guideline",
                "cited_sections": ["1"],
            }
        ],
    }
    template = ReportTemplate.model_validate_json(json.dumps(payload))
    assert template.guideline_references[0].publication_date.isoformat() == "2025-07-01"
    with pytest.raises(ValidationError):
        ReportTemplate.model_validate(payload)
    payload["guideline_references"][0]["publication_date"] = "July 2025"
    with pytest.raises(ValidationError):
        ReportTemplate.model_validate_json(json.dumps(payload))
