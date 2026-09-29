"""Keep study documents, terminology and historical exceptions explicit."""

from pathlib import Path

import yaml

from lx_dtypes.models.interface.data_roots import package_data_root
from lx_dtypes.models.interface.DataLoader import DataLoader
from lx_dtypes.utils.kb_yaml_lint import lint_kb_yaml_files
from lx_dtypes.utils.study_setup_yaml import parse_study_setup_yaml


def test_inventory_covers_every_terminology_manifest() -> None:
    root = package_data_root()
    inventory = yaml.safe_load((root / "definitions.yml").read_text())
    declared = {root / item["manifest"] for item in inventory["terminology"]}
    assert declared == set((root / "terminology").rglob("config.yaml"))
    for item in inventory["terminology"]:
        config = yaml.safe_load((root / item["manifest"]).read_text())
        assert (config["name"], config["version"]) == (item["module"], item["version"])


def test_current_terminology_loads_and_has_no_unclassified_yaml() -> None:
    root = package_data_root()
    terminology = root / "terminology"
    manifests = sorted(
        p
        for p in terminology.rglob("config.yaml")
        if "versions" not in p.relative_to(terminology).parts
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
        for p in terminology.rglob("*")
        if p.suffix in {".yaml", ".yml"}
        and "versions" not in p.relative_to(terminology).parts
    }
    assert current_yaml == selected | set(manifests) | {
        p for p in sidecars if "versions" not in p.relative_to(terminology).parts
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
