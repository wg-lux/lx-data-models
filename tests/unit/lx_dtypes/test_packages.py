from pathlib import Path
from shutil import copytree

import pytest

from lx_dtypes.models.knowledge_base.examination import Examination
from lx_dtypes.models.knowledge_base.finding._Finding import Finding
from lx_dtypes.models.knowledge_base.report_template import (
    ReportFinding,
    ReportTemplate,
    ReportTemplateSection,
)
from lx_dtypes.packages import (
    PackageValidationError,
    create_package,
    load_package,
    validate_package,
)
from lx_dtypes.scripts import lint_kb_yaml
from lx_dtypes.validation import assess_examination


@pytest.fixture
def package(tmp_path: Path) -> Path:
    return create_package(
        tmp_path / "terms",
        name="terms",
        version="1.0.0",
        records=[
            Finding(
                name="lesion",
                name_de="Läsion",
                name_en="Lesion",
                description="Synthetic test finding.",
            ),
            Examination(
                name="exam",
                name_de="Untersuchung",
                name_en="Examination",
                findings=["lesion"],
            ),
        ],
    )


def test_create_load_validate_and_cli_share_contracts(
    package: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    kb = load_package(package)
    payload = {
        "patient": "synthetic",
        "examination": "exam",
        **kb.config.knowledge_base_identity.model_dump(),
    }
    result = validate_package(package, examinations=[payload], language="en")
    assert result.ok
    assert result.examinations == (assess_examination(kb, payload, language="en"),)
    assert result.files == (package.parent / "records.yml",)
    assert "source_file:" not in result.files[0].read_text()
    monkeypatch.setattr("sys.argv", ["ok", "--config", str(package)])
    assert lint_kb_yaml.main() == 0


@pytest.mark.parametrize(
    "change,code",
    [
        ({"examination": "missing"}, "terminology.inadmissible"),
        ({"knowledge_base_version": "2.0.0"}, "terminology.identity_mismatch"),
        ({"examination": None}, "contract.string_type"),
    ],
)
def test_package_assessment_reuses_ledger_failures(
    package: Path, change: dict[str, object], code: str
) -> None:
    payload = {
        "patient": "synthetic",
        "examination": "exam",
        "knowledge_base_module": "terms",
        "knowledge_base_version": "1.0.0",
        **change,
    }
    result = validate_package(package, examinations=[payload])
    assert not result.ok
    assert result.examinations[0].issues[0].code == code


def test_reporting_package_uses_sibling_terminology(package: Path) -> None:
    config = create_package(
        package.parent.parent / "reporting",
        name="reporting",
        version="1.0.0",
        depends_on=["terms"],
        records=[ReportFinding(name="lesion_reference", finding="lesion")],
    )
    kb = load_package(config)
    assert kb.finding["lesion"].kb_module_name == "terms"
    assert kb.report_finding["lesion_reference"].finding == "lesion"


def test_failed_creation_preserves_destination_and_cleans_staging(
    tmp_path: Path,
) -> None:
    with pytest.raises(PackageValidationError):
        create_package(
            tmp_path / "broken",
            name="broken",
            version="1.0.0",
            records=[
                Examination(
                    name="exam",
                    name_de="Untersuchung",
                    name_en="Examination",
                    findings=["missing"],
                )
            ],
        )
    assert list(tmp_path.iterdir()) == []


def test_creation_never_overwrites_existing_package(package: Path) -> None:
    before = package.read_bytes()
    with pytest.raises(FileExistsError):
        create_package(package.parent, name="terms", version="2.0.0")
    assert package.read_bytes() == before


def test_dangling_graph_fails_before_ledger_evaluation(package: Path) -> None:
    records = package.parent / "records.yml"
    records.write_text(records.read_text().replace("- lesion", "- absent"))
    result = validate_package(package, examinations=[{}])
    assert not result.ok
    assert "invalid_knowledge_base" in {issue.code for issue in result.issues}
    assert result.examinations == ()


def test_creation_does_not_mix_concepts_with_reporting(tmp_path: Path) -> None:
    with pytest.raises(PackageValidationError) as error:
        create_package(
            tmp_path / "mixed",
            name="mixed",
            version="1.0.0",
            records=[
                Finding(name="lesion", name_de="Läsion", name_en="Lesion"),
                ReportFinding(name="reference", finding="lesion"),
            ],
        )
    assert "report_template_concept_definition" in {
        issue.code for issue in error.value.result.issues
    }
    assert not (tmp_path / "mixed").exists()


def test_created_template_uses_existing_study_engine(package: Path) -> None:
    config = create_package(
        package.parent.parent / "study",
        name="study",
        version="1.0.0",
        depends_on=["terms"],
        records=[
            ReportTemplateSection(
                name="baseline",
                title_de="Befunde",
                title_en="Findings",
                findings=["lesion"],
            ),
            ReportTemplate(
                name="template",
                name_de="Vorlage",
                name_en="Template",
                examination="exam",
                report_sections=["baseline"],
            ),
        ],
    )
    kb = load_package(config)
    payload = {
        "patient": "synthetic",
        "examination": "exam",
        **kb.config.knowledge_base_identity.model_dump(),
    }
    result = validate_package(config, examinations=[payload], template_name="template")
    assert result.examinations == (
        assess_examination(kb, payload, template_name="template"),
    )
    assert result.examinations[0].study_evaluated


def test_training_package_and_optional_employees_share_runtime_registry(
    tmp_path: Path,
) -> None:
    source = (
        Path(__file__).resolve().parents[3]
        / "docs/examples/dtypes_packages/training_preset"
    )
    root = copytree(source, tmp_path / "training_preset")
    config = root / "config.yaml"
    config.write_text(config.read_text().replace("# - optional/", "- optional/"))
    result = validate_package(config)
    assert result.ok, result.issues
    assert result.knowledge_base is not None
    assert len(result.knowledge_base.study_preset) == 1
    assert len(result.knowledge_base.center_employee_list) == 1


def test_portable_zip_roundtrip_with_external_dependency(
    package: Path, tmp_path: Path
) -> None:
    from lx_dtypes.packages import export_package, import_package

    config = create_package(
        tmp_path / "reporting",
        name="reporting",
        version="1.0.0",
        depends_on=["terms"],
        records=[ReportFinding(name="reference", finding="lesion")],
    )
    (config.parent / "opaque.bin").write_bytes(b"\x00\xffasset")
    archive = export_package(config, tmp_path / "package.zip")
    # Source roots need not be available after transport.
    from shutil import rmtree

    rmtree(config.parent)
    rmtree(package.parent)
    imported = import_package(archive, tmp_path / "installed")
    assert load_package(imported).report_finding["reference"].finding == "lesion"
    assert (imported.parent / "opaque.bin").read_bytes() == b"\x00\xffasset"
    assert (imported.parent / "dependencies/terms/config.yaml").is_file()
    with pytest.raises(FileExistsError):
        import_package(archive, imported.parent)
    with pytest.raises(FileExistsError):
        export_package(imported, archive)


def test_build_isolated_from_ambient_dependencies(
    package: Path, tmp_path: Path
) -> None:
    from lx_dtypes.packages import build_package

    with pytest.raises(PackageValidationError):
        build_package(
            tmp_path / "invalid",
            {
                "config.yaml": "name: missing\nversion: '1.0.0'\ndepends_on: [terms]\ndata: {files: [records.yml]}\n",
                "records.yml": "[]\n",
            },
        )
    assert not (tmp_path / "invalid").exists()


@pytest.mark.parametrize(
    "name", ["../escape", "/absolute", "C:/drive", "bad\\path", "./config.yaml"]
)
def test_import_rejects_unsafe_or_duplicate_names(tmp_path: Path, name: str) -> None:
    from io import BytesIO
    from zipfile import ZipFile

    from lx_dtypes.packages import import_package

    content = BytesIO()
    with ZipFile(content, "w") as archive:
        archive.writestr(
            "config.yaml",
            "name: sample\nversion: '1.0.0'\ndata: {files: [records.yml]}\n",
        )
        archive.writestr("records.yml", "[]\n")
        archive.writestr(name, "bad")
    content.seek(0)
    with pytest.raises(ValueError):
        import_package(content, tmp_path / "invalid")
    assert not (tmp_path / "invalid").exists()


def test_archive_limits_symlinks_and_outer_folder(tmp_path: Path) -> None:
    import stat
    from io import BytesIO
    from zipfile import ZipFile, ZipInfo

    from lx_dtypes.package_archive import read_package_zip
    from lx_dtypes.packages import import_package

    content = BytesIO()
    with ZipFile(content, "w") as archive:
        archive.writestr(
            "outer/config.yaml",
            "name: sample\nversion: '1.0.0'\ndata: {files: [records.yml]}\n",
        )
        archive.writestr("outer/records.yml", "[]\n")
    raw = content.getvalue()
    manifest = import_package(BytesIO(raw), tmp_path / "installed")
    assert load_package(manifest).config.name == "sample"
    for limits in ({"max_files": 1}, {"max_zip_bytes": 1}, {"max_unpacked_bytes": 1}):
        with pytest.raises(ValueError, match="limit|too many"):
            read_package_zip(BytesIO(raw), **limits)
    content = BytesIO()
    with ZipFile(content, "w") as archive:
        link = ZipInfo("config.yaml")
        link.external_attr = (stat.S_IFLNK | 0o777) << 16
        archive.writestr(link, "elsewhere")
    with pytest.raises(ValueError, match="symlinks"):
        import_package(BytesIO(content.getvalue()), tmp_path / "invalid")


def test_export_preserves_nested_layout(package: Path, tmp_path: Path) -> None:
    from lx_dtypes.packages import build_package, export_package_files

    manifest = build_package(
        tmp_path / "nested",
        {
            "config.yaml": "name: bundle\nversion: '1.0.0'\nmodules: [terms]\ndata: {files: [records.yml]}\n",
            "records.yml": "[]\n",
            "terms/config.yaml": package.read_bytes(),
            "terms/records.yml": (package.parent / "records.yml").read_bytes(),
            "terms/asset.bin": b"opaque",
        },
    )
    files = export_package_files(manifest)
    assert files["terms/asset.bin"] == b"opaque"
    assert "terms/config.yaml" in files
    assert not any(name.startswith("dependencies/") for name in files)


def test_registered_package_retains_separate_explicit_dependency_roots(
    package: Path, tmp_path: Path
) -> None:
    from lx_dtypes.packages import export_package_files, load_registered_package
    from lx_dtypes.terminology.terminology_service import TerminologyService

    config = create_package(
        tmp_path / "reporting",
        name="reporting",
        version="1.0.0",
        depends_on=["terms"],
        records=[ReportFinding(name="reference", finding="lesion")],
    )
    moved = tmp_path / "elsewhere/reporting"
    moved.parent.mkdir()
    config.parent.rename(moved)
    service = TerminologyService(tmp_path / "registry.json")
    service.register_local("reporting", "1.0.0", input_dirs=[moved, package.parent])
    kb = load_registered_package("reporting", version="1.0.0", service=service)
    assert kb.report_finding["reference"].finding == "lesion"
    files = export_package_files(
        moved / "config.yaml", input_dirs=service.source_paths("reporting", "1.0.0")
    )
    assert "dependencies/terms/config.yaml" in files
    records = moved / "records.yml"
    records.write_text(records.read_text() + "  unexpected_field: invalid\n")
    with pytest.raises(PackageValidationError):
        load_registered_package("reporting", version="1.0.0", service=service)


def test_archive_bytes_are_reproducible(package: Path) -> None:
    from io import BytesIO
    from zipfile import ZipFile

    from lx_dtypes.packages import package_archive_bytes

    first = package_archive_bytes(package)
    assert first == package_archive_bytes(package)
    with ZipFile(BytesIO(first)) as archive:
        assert all(
            info.date_time == (1980, 1, 1, 0, 0, 0) for info in archive.infolist()
        )


def test_failed_archive_publication_leaves_no_partial_file(
    package: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from lx_dtypes.packages import export_package

    def fail(*args: object, **kwargs: object) -> None:
        raise OSError("publication unavailable")

    monkeypatch.setattr("lx_dtypes.packages.os.link", fail)
    with pytest.raises(OSError, match="publication unavailable"):
        export_package(package, tmp_path / "output.zip")
    assert not (tmp_path / "output.zip").exists()
    assert not list(tmp_path.glob(".lx-package-*"))


def test_failed_folder_publication_cleans_reserved_destination(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from lx_dtypes.packages import build_package

    def fail(*args: object, **kwargs: object) -> None:
        raise OSError("publication unavailable")

    monkeypatch.setattr(Path, "rename", fail)
    with pytest.raises(OSError, match="publication unavailable"):
        build_package(
            tmp_path / "output",
            {
                "config.yaml": "name: sample\nversion: '1.0.0'\ndata: {files: [records.yml]}\n",
                "records.yml": "[]\n",
            },
        )
    assert list(tmp_path.iterdir()) == []


def test_registered_reads_emit_historical_authoring_warnings(tmp_path: Path) -> None:
    from lx_dtypes.packages import PackageAuthoringWarning, load_registered_package
    from lx_dtypes.terminology.terminology_service import TerminologyService

    root = tmp_path / "historical"
    root.mkdir()
    (root / "config.yaml").write_text(
        "name: historical\nversion: '1.0.0'\ndata: {files: [records.yml]}\n"
    )
    (root / "records.yml").write_text("- model: examination\n  name: exam\n")
    service = TerminologyService(tmp_path / "registry.json")
    service.register_local("historical", "1.0.0", input_dirs=[root])
    with pytest.warns(PackageAuthoringWarning, match="coverage"):
        kb = load_registered_package("historical", version="1.0.0", service=service)
    assert "exam" in kb.examination
    with pytest.raises(PackageValidationError):
        load_package(root / "config.yaml")
