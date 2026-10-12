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
            module_files, strict_aliases=True, strict_mixed_styles=True
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
