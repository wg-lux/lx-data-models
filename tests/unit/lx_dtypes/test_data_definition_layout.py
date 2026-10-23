"""Keep study documents, terminology, reports and historical exceptions explicit."""

from pathlib import Path

import pytest
import yaml

from lx_dtypes.models.interface.data_roots import package_data_root
from lx_dtypes.models.interface.DataLoader import DataLoader
from lx_dtypes.utils.kb_yaml_lint import discover_yaml_files, lint_kb_yaml_files
from lx_dtypes.utils.study_setup_yaml import parse_study_setup_yaml


def test_inventory_covers_every_definition_manifest() -> None:
    root = package_data_root()
    inventory = yaml.safe_load((root / "definitions.yml").read_text())
    declared = {
        root / item["manifest"]
        for item in inventory["terminology"] + inventory["report_templates"]
    }
    assert declared == set(root.rglob("config.yaml"))
    for item in inventory["terminology"] + inventory["report_templates"]:
        config = yaml.safe_load((root / item["manifest"]).read_text())
        assert (config["name"], config["version"]) == (item["module"], item["version"])


def test_current_definitions_load_and_have_no_unclassified_yaml() -> None:
    root = package_data_root()
    manifests = sorted(
        p
        for p in root.rglob("config.yaml")
        if "versions" not in p.relative_to(root).parts
    )
    loader = DataLoader(input_dirs=[p.parent for p in manifests])
    selected: set[Path] = set()
    for manifest in manifests:
        config = yaml.safe_load(manifest.read_text())
        kb = loader.load_knowledge_base(config["name"])
        assert (kb.config.name, kb.config.version) == (
            config["name"],
            config["version"],
        )
        module_files: set[Path] = set()
        for resolved in loader.resolved_module_configs(config["name"]):
            module_files.update(resolved.data.get_files_with_suffix(".yaml"))
            module_files.update(resolved.data.get_files_with_suffix(".yml"))
        assert not lint_kb_yaml_files(
            module_files,
            strict_aliases=True,
            strict_mixed_styles=True,
            check_authoring=True,
        )
        selected.update(module_files)
    inventory = yaml.safe_load((root / "definitions.yml").read_text())
    sidecars = {root / item["path"] for item in inventory["sidecars"]}
    current_yaml = {
        p
        for category in ("terminology", "report_templates")
        for p in (root / category).rglob("*")
        if p.suffix in {".yaml", ".yml"} and "versions" not in p.relative_to(root).parts
    }
    assert current_yaml == selected | set(manifests) | {
        p for p in sidecars if "versions" not in p.relative_to(root).parts
    }
    assert not list(root.rglob("*.csv"))


def test_study_documents_are_separate_and_validate() -> None:
    root = package_data_root()
    inventory = yaml.safe_load((root / "definitions.yml").read_text())
    paths = {root / item["path"] for item in inventory["study_metadata"]}
    assert paths == set((root / "study_metadata").glob("*.yml"))
    for path in paths:
        setup = parse_study_setup_yaml(path.read_text())
        assert setup.cohorts
    assert not list((root / "study_metadata").rglob("config.yaml"))


def test_current_reporting_and_terminology_records_are_separate() -> None:
    root = package_data_root()
    reporting_models = {"report_template", "report_template_section", "report_finding"}
    validator_models = {
        "classification_validator",
        "findings_validator",
        "examination_validator",
        "intervention_validator",
        "unit_validator",
    }
    for category in ("terminology", "report_templates"):
        for path in (root / category).rglob("*"):
            if path.suffix not in {".yaml", ".yml"} or "versions" in path.parts:
                continue
            records = yaml.safe_load(path.read_text())
            if not isinstance(records, list):
                continue  # Manifests and declared sidecars are mappings.
            models = {record["model"] for record in records}
            if category == "report_templates":
                assert models <= reporting_models | validator_models, path
            else:
                assert not models & reporting_models, path
    # Terminology is independently loadable: it never depends on report packages.
    manifests = [
        p
        for p in (root / "terminology").rglob("config.yaml")
        if "versions" not in p.relative_to(root).parts
    ]
    loader = DataLoader(input_dirs=[p.parent for p in manifests])
    for manifest in manifests:
        kb = loader.load_knowledge_base(yaml.safe_load(manifest.read_text())["name"])
        assert not kb.report_template
        assert not kb.report_template_section
        assert not kb.report_finding


@pytest.mark.parametrize(
    "module",
    [
        "coloreg",
        "star_upper_gi",
        "mst_3_0",
        "dgvs_reporting",
        "report_template_examples",
    ],
)
def test_report_manifest_lint_resolves_terminology_dependencies(module: str) -> None:
    manifest = package_data_root() / "report_templates" / module / "config.yaml"
    files, issues = discover_yaml_files(paths=[], config_paths=[manifest])
    assert not issues
    assert not lint_kb_yaml_files(files, strict_aliases=True, strict_mixed_styles=True)


def test_current_modules_have_explicit_sources() -> None:
    root = package_data_root()
    inventory = yaml.safe_load((root / "definitions.yml").read_text())
    provenance = inventory["source_provenance"]
    current_modules = {
        yaml.safe_load(path.read_text())["name"]
        for path in root.rglob("config.yaml")
        if "versions" not in path.relative_to(root).parts
    }
    assert set(provenance["module_sources"]) == current_modules
    for source_ids in provenance["module_sources"].values():
        assert source_ids
        assert set(source_ids) <= provenance["sources"].keys()
    for source in provenance["sources"].values():
        assert source["authority"] and source["scope"]
        if "canonical_document" in source:
            assert Path(source["canonical_document"]).is_file()
        if "url" in source:
            assert source["url"].startswith("https://")


def test_legacy_unit_wrapper_composes_with_canonical_units(tmp_path: Path) -> None:
    (tmp_path / "config.yaml").write_text(
        yaml.safe_dump(
            {
                "name": "unit_composition",
                "version": "1.0.0",
                "depends_on": ["lx_units", "lx_utils_units"],
                "data": {"files": [], "dirs": []},
            }
        )
    )
    loader = DataLoader(
        input_dirs=[
            package_data_root() / "terminology" / "lx_units",
            package_data_root() / "terminology" / "lx_utils",
            tmp_path,
        ]
    )
    canonical = loader.load_knowledge_base("lx_units")
    combined = loader.load_knowledge_base("unit_composition")
    assert combined.unit.keys() == canonical.unit.keys()
    for name, unit in canonical.unit.items():
        assert combined.unit[name].model_dump(
            exclude={"created_at", "uuid"}
        ) == unit.model_dump(exclude={"created_at", "uuid"})
    assert all(unit.kb_module_name == "lx_units" for unit in combined.unit.values())


@pytest.mark.parametrize(
    ("manifest", "expected"),
    [
        ("data/terminology/lx_utils/unit/config.yaml", "data"),
        ("data/report_templates/coloreg/config.yaml", "data"),
        (
            "data/terminology/versions/coloreg/0.1.0/coloreg/config.yaml",
            "data/terminology/versions/coloreg/0.1.0",
        ),
        ("custom/modules/unit/config.yaml", "custom/modules"),
    ],
)
def test_module_search_scope_preserves_release_isolation(
    manifest: str, expected: str
) -> None:
    from lx_dtypes.models.interface.data_roots import module_search_root

    assert module_search_root(Path(manifest)) == Path(expected)
