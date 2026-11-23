"""Package kinds through export, import, registry listing and channel installs."""

import json
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from shutil import copytree
from zipfile import ZipFile

import pytest
import yaml

from lx_dtypes.knowledge_bases import (
    get_packaged_knowledge_base,
    list_packaged_knowledge_bases,
)
from lx_dtypes.models.contracts import PackageChannelEntry, PackageKind
from lx_dtypes.models.interface.KnowledgeBase import KnowledgeBase
from lx_dtypes.models.interface.KnowledgeBaseResolver import (
    clear_knowledge_base_resolver_caches,
    load_knowledge_base,
)
from lx_dtypes.models.knowledge_base import KB_MODEL_NAMES_ORDERED
from lx_dtypes.models.knowledge_base.examination import Examination
from lx_dtypes.models.knowledge_base.finding._Finding import Finding
from lx_dtypes.models.knowledge_base.report_template import (
    ReportFinding,
    ReportTemplateSection,
)
from lx_dtypes.models.knowledge_base.validators import FindingsValidator
from lx_dtypes.package_archive import PackageArchiveError
from lx_dtypes.package_kinds import LEGACY_KIND_MODEL_GROUPS
from lx_dtypes.packages import (
    PackageValidationError,
    audit_package_kind_dependencies,
    audit_packaged_kind_dependencies,
    create_package,
    import_package,
    infer_legacy_package_kind,
    install_channel_package,
    load_package,
    package_archive_bytes,
    read_package_archive,
)
from lx_dtypes.terminology.terminology_service import (
    TerminologyError,
    TerminologyService,
)
from lx_dtypes.utils.parser import camel_to_snake
from tests.paths import PACKAGE_ROOT

# Reviewed classification of every shipped catalog release (contract v1).
REVIEWED_KINDS = {
    ("dgvs_reporting", "0.2.0"): "report_templates",
    ("dgvs_reporting", "0.1.0"): "report_templates",
    ("coloreg", "0.1.0"): "report_templates",
    ("coloreg", "0.2.0"): "report_templates",
    ("coloreg", "0.3.0"): "report_templates",
    ("mst_3_0", "3.0.0"): "report_templates",
    ("star_upper_gi", "0.1.2"): "report_templates",
    ("star_upper_gi", "0.1.1.post1"): "report_templates",
    ("report_medications", "0.1.0"): "report_templates",
    ("report_electrosurgery", "0.1.0"): "report_templates",
    ("polyp_size_category", "1.0.0"): "terminology",
    ("polyp_size_category", "2.0.0"): "terminology",
    ("coloreg_terminology", "0.3.0"): "terminology",
    ("mst_3_0_terminology", "3.0.0"): "terminology",
    ("report_template_examples_terminology", "0.1.1"): "terminology",
    ("star_upper_gi_terminology", "0.1.2"): "terminology",
    ("endoreg_reference", "1.0.0"): "application_data",
    ("endoreg_reference", "1.1.0"): "application_data",
    ("endoreg_workforce", "1.0.0"): "application_data",
    ("endoreg_green_endoscopy", "1.0.0"): "application_data",
    ("DGVS_Terminology", "0.1.0"): "terminology",
    ("lx_units", "0.1.0"): "terminology",
    ("lx_descriptors", "0.1.0"): "terminology",
    ("lx_classification_choices", "0.1.0"): "terminology",
    ("lx_classifications", "0.1.0"): "terminology",
    ("lx_interventions", "0.1.0"): "terminology",
    ("lx_findings", "0.1.0"): "terminology",
    ("lx_indications", "0.1.0"): "terminology",
    ("information_source_data", "0.1.0"): "terminology",
    ("lx_utils", "0.1.0"): "terminology",
    ("lx_hardware", "0.1.0"): "terminology",
    ("lx_examinations", "0.1.0"): "terminology",
}


@pytest.fixture(autouse=True)
def isolated_caches():
    clear_knowledge_base_resolver_caches()
    yield
    clear_knowledge_base_resolver_caches()


def _declare(config: Path, kind: str | None) -> Path:
    if kind is not None:
        with config.open("a", encoding="utf-8") as handle:
            handle.write(f"package_kind: {kind}\n")
    return config


def _terms(root: Path, kind: str | None = "terminology") -> Path:
    config = create_package(
        root / "terms",
        name="terms",
        version="1.0.0",
        records=[
            Finding(
                name="lesion",
                name_de="Läsion",
                name_en="Lesion",
                description="Synthetic test finding.",
            )
        ],
    )
    return _declare(config, kind)


def _zip(files: dict[str, bytes]) -> bytes:
    content = BytesIO()
    with ZipFile(content, "w") as archive:
        for name, data in sorted(files.items()):
            archive.writestr(name, data)
    return content.getvalue()


def _manifest(**changes: str) -> bytes:
    return json.dumps(
        {
            "schema": "lx-package/1",
            "name": "terms",
            "version": "1.0.0",
            "package_kind": "terminology",
            **changes,
        }
    ).encode()


def _files(archive: bytes) -> dict[str, bytes]:
    with ZipFile(BytesIO(archive)) as opened:
        return {name: opened.read(name) for name in opened.namelist()}


def test_catalog_classifies_every_shipped_release() -> None:
    catalog = {
        (item.module_name, item.version): item.package_kind
        for item in list_packaged_knowledge_bases()
    }
    assert catalog == {
        identity: PackageKind(kind) for identity, kind in REVIEWED_KINDS.items()
    }


def test_export_writes_manifest_matching_declared_config(tmp_path: Path) -> None:
    config = _terms(tmp_path)
    files = _files(package_archive_bytes(config))
    manifest = json.loads(files["lx-package.json"])
    assert manifest == {
        "schema": "lx-package/1",
        "name": "terms",
        "version": "1.0.0",
        "package_kind": "terminology",
    }
    assert "\npackage_kind: terminology\n" in files["config.yaml"].decode()


def test_export_of_unclassified_package_has_no_manifest(tmp_path: Path) -> None:
    files = _files(package_archive_bytes(_terms(tmp_path, kind=None)))
    assert "lx-package.json" not in files


def test_export_rewrites_matching_root_manifest_canonically(tmp_path: Path) -> None:
    config = _terms(tmp_path)
    expected = _files(package_archive_bytes(config))["lx-package.json"]
    # Editors may write their own formatting; agreement is what matters.
    (config.parent / "lx-package.json").write_text(
        json.dumps(json.loads(expected), indent=None), encoding="utf-8"
    )
    assert _files(package_archive_bytes(config))["lx-package.json"] == expected


@pytest.mark.parametrize(
    "manifest",
    [
        _manifest(package_kind="report_templates"),
        _manifest(version="2.0.0"),
        b"{not json",
    ],
)
def test_export_rejects_disagreeing_root_manifest(
    tmp_path: Path, manifest: bytes
) -> None:
    config = _terms(tmp_path)
    (config.parent / "lx-package.json").write_bytes(manifest)
    # The authoring gate (package_manifest_mismatch) or the archive check rejects it.
    with pytest.raises((PackageArchiveError, PackageValidationError)):
        package_archive_bytes(config)


def test_export_rejects_manifest_for_unclassified_config(tmp_path: Path) -> None:
    config = _terms(tmp_path, kind=None)
    (config.parent / "lx-package.json").write_bytes(_manifest())
    with pytest.raises(
        (PackageArchiveError, PackageValidationError), match="package_kind"
    ):
        package_archive_bytes(config)


def test_import_roundtrip_keeps_kind(tmp_path: Path) -> None:
    archive = package_archive_bytes(_terms(tmp_path / "source"))
    imported = import_package(BytesIO(archive), tmp_path / "installed")
    assert "package_kind: terminology" in imported.read_text(encoding="utf-8")
    assert (imported.parent / "lx-package.json").is_file()


@pytest.mark.parametrize(
    "field,value",
    [
        ("name", "other"),
        ("version", "9.9.9"),
        ("package_kind", "report_templates"),
    ],
)
def test_import_rejects_manifest_mismatch(
    tmp_path: Path, field: str, value: str
) -> None:
    files = _files(package_archive_bytes(_terms(tmp_path / "source")))
    files["lx-package.json"] = _manifest(**{field: value})
    with pytest.raises(PackageArchiveError, match=field):
        read_package_archive(BytesIO(_zip(files)))
    service = TerminologyService(registry_path=tmp_path / "registry" / "r.json")
    with pytest.raises(TerminologyError, match=field) as error:
        service.import_zip(BytesIO(_zip(files)))
    assert error.value.status == 400
    assert not service.registry_path.exists()


def test_legacy_zip_without_manifest_imports_and_migrates(tmp_path: Path) -> None:
    files = _files(package_archive_bytes(_terms(tmp_path / "source", kind=None)))
    assert "lx-package.json" not in files
    read_package_archive(BytesIO(_zip(files)))
    service = TerminologyService(registry_path=tmp_path / "registry" / "r.json")
    imported = service.import_zip(BytesIO(_zip(files))).imported
    assert (imported.package_kind, imported.package_kind_source) == (
        PackageKind.terminology,
        "migrated",
    )
    listed = service.list_bundles().bundles
    assert [(b.module_name, b.package_kind_source) for b in listed] == [
        ("terms", "migrated")
    ]
    # Migration is reported, never written into the registry or package files.
    entry = json.loads(service.registry_path.read_text())["modules"]["terms"]["1.0.0"]
    assert "package_kind" not in entry
    installed = service.source_paths("terms", "1.0.0")[0] / "terms" / "config.yaml"
    assert "package_kind" not in installed.read_text(encoding="utf-8")


def test_legacy_zip_kind_comes_from_config(tmp_path: Path) -> None:
    files = _files(package_archive_bytes(_terms(tmp_path / "source")))
    del files["lx-package.json"]
    service = TerminologyService(registry_path=tmp_path / "registry" / "r.json")
    assert (
        service.import_zip(BytesIO(_zip(files))).imported.package_kind
        is PackageKind.terminology
    )
    entry = json.loads(service.registry_path.read_text())["modules"]["terms"]["1.0.0"]
    assert entry["package_kind"] == "terminology"


def test_listing_exposes_local_declared_unclassified_and_shipped_kinds(
    tmp_path: Path,
) -> None:
    config = _terms(tmp_path / "packages")
    reporting = _declare(
        create_package(
            tmp_path / "packages" / "reporting",
            name="reporting",
            version="1.0.0",
            depends_on=["terms"],
            records=[
                ReportFinding(name="reference", name_de="Verweis", finding="lesion")
            ],
        ),
        None,
    )
    service = TerminologyService(registry_path=tmp_path / "registry" / "r.json")
    service.register_local("terms", "1.0.0", input_dirs=[config.parent.parent])
    service.register_local("reporting", "1.0.0", input_dirs=[reporting.parent.parent])
    shipped = get_packaged_knowledge_base("polyp_size_category", "2.0.0")
    payload = json.loads(service.registry_path.read_text())
    payload["modules"]["polyp_size_category"] = {
        "2.0.0": {
            "medical_field": "gastroenterology",
            "sources": [
                {
                    "kind": "provider",
                    "provider": "lx_dtypes.builtin",
                    "content_sha256": shipped.content_sha256,
                }
            ],
        }
    }
    service.registry_path.write_text(json.dumps(payload))
    kinds = {
        bundle.module_name: (bundle.package_kind, bundle.package_kind_source)
        for bundle in service.list_bundles().bundles
    }
    # A report_finding alone does not determine a kind: unclassified, not guessed.
    assert kinds == {
        "terms": (PackageKind.terminology, "declared"),
        "reporting": (None, None),
        "polyp_size_category": (PackageKind.terminology, "catalog"),
    }
    # Listings serialize the kind as its plain string value or null.
    dumped = service.list_bundles().model_dump(mode="json")
    assert {b["module_name"]: b["package_kind"] for b in dumped["bundles"]} == {
        "terms": "terminology",
        "reporting": None,
        "polyp_size_category": "terminology",
    }


def test_listing_rejects_conflicting_declarations(tmp_path: Path) -> None:
    config = _terms(tmp_path / "packages")
    service = TerminologyService(registry_path=tmp_path / "registry" / "r.json")
    service.register_local("terms", "1.0.0", input_dirs=[config.parent.parent])
    payload = json.loads(service.registry_path.read_text())
    payload["modules"]["terms"]["1.0.0"]["package_kind"] = "application_data"
    service.registry_path.write_text(json.dumps(payload))
    with pytest.raises(TerminologyError, match="conflicting package kinds"):
        service.list_bundles()


def _channel_entry(payload: bytes, **changes: object) -> PackageChannelEntry:
    digest = sha256(payload).hexdigest()
    return PackageChannelEntry.model_validate(
        {
            "name": "terms",
            "version": "1.0.0",
            "package_kind": "terminology",
            "sha256": digest,
            "size": len(payload),
            "path": f"packages/{digest}.zip",
            "published_at": "2026-11-20T10:00:00Z",
            **changes,
        }
    )


def test_channel_install_verifies_bytes_then_imports(tmp_path: Path) -> None:
    payload = package_archive_bytes(_terms(tmp_path / "source"))
    service = TerminologyService(registry_path=tmp_path / "registry" / "r.json")
    result = install_channel_package(_channel_entry(payload), payload, service=service)
    assert result.imported.package_kind is PackageKind.terminology
    assert service.active_identity() is None


def test_channel_install_rejects_integrity_and_identity_failures(
    tmp_path: Path,
) -> None:
    payload = package_archive_bytes(_terms(tmp_path / "source"))
    service = TerminologyService(registry_path=tmp_path / "registry" / "r.json")
    entry = _channel_entry(payload)
    with pytest.raises(TerminologyError, match="size"):
        install_channel_package(entry, payload + b"\0", service=service)
    tampered = bytearray(payload)
    tampered[-1] ^= 0xFF
    with pytest.raises(TerminologyError, match="SHA-256"):
        install_channel_package(entry, bytes(tampered), service=service)
    with pytest.raises(TerminologyError, match="channel entry"):
        install_channel_package(
            _channel_entry(payload, package_kind="report_templates"),
            payload,
            service=service,
        )
    legacy_files = _files(payload)
    del legacy_files["lx-package.json"]
    legacy = _zip(legacy_files)
    with pytest.raises(TerminologyError, match="require a root lx-package.json"):
        install_channel_package(_channel_entry(legacy), legacy, service=service)
    assert not service.registry_path.exists()


def test_audit_reports_violations_and_unclassified_edges(tmp_path: Path) -> None:
    terms = _terms(tmp_path / "packages", kind="study")
    reporting = _declare(
        create_package(
            tmp_path / "packages" / "reporting",
            name="reporting",
            version="1.0.0",
            depends_on=["terms"],
            records=[
                ReportFinding(name="reference", name_de="Verweis", finding="lesion")
            ],
        ),
        "report_templates",
    )
    findings = audit_package_kind_dependencies(reporting)
    assert [(f.status, f.module, f.dependency) for f in findings] == [
        ("violation", "reporting", "terms")
    ]
    assert "report_templates" in findings[0].format()
    terms.write_text(terms.read_text().replace("package_kind: study\n", ""))
    unclassified = audit_package_kind_dependencies(reporting)
    assert [f.status for f in unclassified] == ["unclassified"]
    allowed = audit_package_kind_dependencies(
        reporting, package_kinds={("terms", "1.0.0"): PackageKind.terminology}
    )
    assert allowed == ()


def test_shipped_catalog_audit_matches_reported_violations() -> None:
    violations = {
        (f.module, f.version, f.dependency, f.dependency_version)
        for f in audit_packaged_kind_dependencies()
        if f.status == "violation"
    }
    # terminology and report_templates may depend on application_data.
    assert violations == set()


def _load(config: Path) -> KnowledgeBase:
    clear_knowledge_base_resolver_caches()
    return load_knowledge_base(
        yaml.safe_load(config.read_text())["name"],
        version="1.0.0",
        input_dirs=[config.parent.parent],
    )


def test_legacy_inference_groups_cover_every_record_model() -> None:
    grouped = [model for group in LEGACY_KIND_MODEL_GROUPS.values() for model in group]
    assert len(grouped) == len(set(grouped))
    assert set(grouped) == {camel_to_snake(name) for name in KB_MODEL_NAMES_ORDERED}


def test_legacy_inference_terminology_and_report_templates(tmp_path: Path) -> None:
    terms = _terms(tmp_path / "packages", kind=None)
    result = infer_legacy_package_kind(_load(terms))
    assert result.package_kind is PackageKind.terminology
    assert "finding=1" in result.reason
    reporting = create_package(
        tmp_path / "packages" / "reporting",
        name="reporting",
        version="1.0.0",
        depends_on=["terms"],
        records=[
            ReportFinding(name="reference", name_de="Verweis", finding="lesion"),
            ReportTemplateSection(
                name="section",
                name_de="Abschnitt",
                title_de="B",
                title_en="F",
                findings=["reference"],
            ),
        ],
    )
    # Dependency records (the terminology finding) are not the package's own.
    inferred = infer_legacy_package_kind(_load(reporting))
    assert inferred.package_kind is PackageKind.report_templates
    assert "finding=" not in inferred.reason.replace("report_finding=", "")


def test_legacy_inference_application_data_study_mixed_and_empty(
    tmp_path: Path,
) -> None:
    workforce = get_packaged_knowledge_base("endoreg_workforce")
    kb = load_knowledge_base(
        "endoreg_workforce",
        version=workforce.version,
        input_dirs=[workforce.installed_data_root()],
    )
    assert infer_legacy_package_kind(kb).package_kind is PackageKind.application_data

    preset = tmp_path / "training_preset"
    copytree(
        PACKAGE_ROOT.parent / "docs/examples/dtypes_packages/training_preset", preset
    )
    clear_knowledge_base_resolver_caches()
    study = load_knowledge_base(
        "training_preset", version="1.0.0", input_dirs=[preset.parent]
    )
    assert infer_legacy_package_kind(study).package_kind is PackageKind.study

    terms = _terms(tmp_path / "packages", kind=None)
    shift_types = (
        Path(str(workforce.resource_directory())) / "shift_type.yml"
    ).read_text(encoding="utf-8")
    records = terms.parent / "records.yml"
    records.write_text(records.read_text() + shift_types, encoding="utf-8")
    mixed = infer_legacy_package_kind(_load(terms))
    assert mixed.package_kind is None
    assert "reference_catalog=1" in mixed.reason and "finding=1" in mixed.reason

    empty = tmp_path / "empty" / "empty"
    empty.mkdir(parents=True)
    (empty / "config.yaml").write_text("name: empty\nversion: '1.0.0'\n")
    assert infer_legacy_package_kind(_load(empty / "config.yaml")).package_kind is None


def _validator_packages(
    root: Path, template_validators: list[str], local: list[FindingsValidator]
) -> Path:
    create_package(
        root / "terms",
        name="terms",
        version="1.0.0",
        records=[
            Finding(name="lesion", name_de="L", name_en="L", description="x"),
            Examination(name="exam", name_de="U", name_en="E", findings=["lesion"]),
            FindingsValidator(
                name="lesion_present",
                name_de="Befund vorhanden",
                name_en="Finding present",
                finding="lesion",
                operator="exists",
            ),
        ],
    )
    directory = root / "reporting"
    directory.mkdir()
    (directory / "config.yaml").write_text(
        yaml.safe_dump(
            {
                "name": "reporting",
                "version": "1.0.0",
                "package_kind": "report_templates",
                "depends_on": ["terms"],
                "data": {"files": ["records.yml"]},
            }
        )
    )
    records: list[dict[str, object]] = [
        {
            "model": "report_finding",
            "name": "lesion_ref",
            "name_de": "Läsionsverweis",
            "finding": "lesion",
        },
        {
            "model": "report_template_section",
            "name": "section",
            "name_de": "Abschnitt",
            "title_de": "B",
            "title_en": "F",
            "findings": ["lesion_ref"],
        },
        {
            "model": "report_template",
            "name": "template",
            "name_de": "Vorlage",
            "name_en": "Template",
            "examination": "exam",
            "report_sections": ["section"],
            "validators": {"findings_validators": template_validators},
        },
        *(
            {
                "model": "findings_validator",
                **v.model_dump(mode="json", exclude_unset=True),
            }
            for v in local
        ),
    ]
    (directory / "records.yml").write_text(yaml.safe_dump(records))
    return directory / "config.yaml"


def test_template_calls_terminology_validator_from_dependency(tmp_path: Path) -> None:
    config = _validator_packages(tmp_path, ["lesion_present"], [])
    kb = load_package(config)
    assert kb.findings_validator["lesion_present"].kb_module_name == "terms"
    assert kb.unresolved_template_validator_references() == ()


def test_report_templates_package_carries_custom_validator(tmp_path: Path) -> None:
    custom = FindingsValidator(
        name="lesion_missing_local",
        name_de="Lokale Regel",
        name_en="Local rule",
        finding="lesion",
        operator="missing",
    )
    config = _validator_packages(
        tmp_path, ["lesion_present", "lesion_missing_local"], [custom]
    )
    kb = load_package(config)
    assert kb.findings_validator["lesion_missing_local"].kb_module_name == "reporting"
    assert kb.findings_validator["lesion_present"].operator == "exists"


def test_divergent_validator_with_central_name_fails_closed(tmp_path: Path) -> None:
    divergent = FindingsValidator(
        name="lesion_present",
        name_de="Abweichend",
        name_en="Divergent",
        finding="lesion",
        operator="missing",
    )
    config = _validator_packages(tmp_path, ["lesion_present"], [divergent])
    with pytest.raises(PackageValidationError, match="lesion_present"):
        load_package(config)
    clear_knowledge_base_resolver_caches()
    with pytest.raises(ValueError, match="Conflicting 'findings_validator'"):
        load_knowledge_base("reporting", version="1.0.0", input_dirs=[tmp_path])


def test_unresolved_template_validator_fails_loading(tmp_path: Path) -> None:
    config = _validator_packages(tmp_path, ["not_defined_anywhere"], [])
    with pytest.raises(PackageValidationError, match="not_defined_anywhere"):
        load_package(config)
    clear_knowledge_base_resolver_caches()
    with pytest.raises(ValueError, match="missing findings_validator"):
        load_knowledge_base("reporting", version="1.0.0", input_dirs=[tmp_path])


def test_legacy_inference_accepts_validated_config_path(tmp_path: Path) -> None:
    archive = package_archive_bytes(_terms(tmp_path / "source", kind=None))
    imported = import_package(BytesIO(archive), tmp_path / "installed")
    result = infer_legacy_package_kind(imported)
    assert result.package_kind is PackageKind.terminology
    assert result.reason
    with pytest.raises(TypeError):
        infer_legacy_package_kind(load_package(imported), input_dirs=[tmp_path])


def test_legacy_inference_counts_composed_modules_not_dependencies(
    tmp_path: Path,
) -> None:
    root = tmp_path / "legacy"
    (root / "terms").mkdir(parents=True)
    (root / "config.yaml").write_text(
        "name: legacy\nversion: '1.0'\nmodules: [terms]\n"
    )
    (root / "terms" / "config.yaml").write_text(
        "name: terms\nversion: '1.0'\ndata:\n  files: [records.yml]\n"
    )
    (root / "terms" / "records.yml").write_text(
        "- model: finding\n  name: example\n  name_de: Beispiel\n  name_en: Example\n"
    )
    composed = infer_legacy_package_kind(root / "config.yaml")
    assert composed.package_kind is PackageKind.terminology
    (root / "config.yaml").write_text(
        "name: legacy\nversion: '1.0'\ndepends_on: [terms]\n"
    )
    clear_knowledge_base_resolver_caches()
    assert infer_legacy_package_kind(root / "config.yaml").package_kind is None
