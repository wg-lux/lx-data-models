from pathlib import Path

import pytest

from lx_dtypes.models.interface.DataLoader import (
    AmbiguousModuleConfigError,
    DataLoader,
    ModuleConfigNotFoundError,
)
from lx_dtypes.models.interface.KnowledgeBaseConfig import KnowledgeBaseConfig
from lx_dtypes.utils.dataloader import resolve_kb_module_load_order


def _write_module_config(
    module_dir: Path,
    *,
    name: str,
    version: str = "0.1.0",
    modules: list[str] | None = None,
    depends_on: list[str] | None = None,
    data_dirs: list[str] | None = None,
) -> None:
    module_dir.mkdir(parents=True, exist_ok=True)
    lines = [
        f"name: {name}",
        'description: ""',
        f"version: {version}",
    ]
    if modules:
        lines.extend(["modules:", *[f"  - {module}" for module in modules]])
    else:
        lines.append("modules: []")
    if depends_on:
        lines.extend(
            ["depends_on:", *[f"  - {dependency}" for dependency in depends_on]]
        )
    else:
        lines.append("depends_on: []")
    if data_dirs is not None:
        lines.append("data:")
        if data_dirs:
            lines.extend(["  dirs:", *[f"    - {data_dir}" for data_dir in data_dirs]])
        else:
            lines.append("  dirs: []")
    (module_dir / "config.yaml").write_text("\n".join(lines) + "\n")


def _write_unit(module_dir: Path, *, name: str, abbreviation: str) -> None:
    data_dir = module_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / "units.yaml").write_text(
        "\n".join(
            [
                "- model: unit",
                f"  name: {name}",
                f"  abbreviation: {abbreviation}",
            ]
        )
        + "\n"
    )


def _write_minimal_module_config(module_dir: Path, *, module_name: str) -> None:
    module_dir.mkdir(parents=True, exist_ok=True)
    (module_dir / "config.yaml").write_text(
        "\n".join(
            [
                f"name: {module_name}",
                'description: ""',
                "version: 0.1.0",
                "modules: []",
                "depends_on: []",
            ]
        )
        + "\n"
    )


class TestDataLoader:
    def test_data_loader_fetch_config_yamls(
        self,
        yaml_data_loader: DataLoader,
    ) -> None:
        config_files = yaml_data_loader.fetch_config_yamls()
        # logger.info(f"Found {len(config_files)} config.yaml files in data loader input dirs.")
        assert isinstance(config_files, list)
        for config_file in config_files:
            assert config_file.name == "config.yaml"
            assert config_file.exists()

    def test_get_initialized_config_missing_module(
        self, empty_data_loader: DataLoader
    ) -> None:
        with pytest.raises(ValueError, match="is not loaded"):
            empty_data_loader.get_initialized_config("unknown")

    def test_get_initialized_config_missing_dependency(
        self, empty_data_loader: DataLoader
    ) -> None:
        root = KnowledgeBaseConfig(name="root", version="1.0.0", modules=["mod_a"])
        mod_a = KnowledgeBaseConfig(
            name="mod_a", version="1.0.0", depends_on=["ghost"], modules=[]
        )
        empty_data_loader.module_configs = {
            root.name: root,
            mod_a.name: mod_a,
        }

        with pytest.raises(
            ModuleConfigNotFoundError,
            match="referenced but no configuration",
        ):
            empty_data_loader.get_initialized_config("root")

    def test_root_module_with_multiple_config_candidates_is_ambiguous(
        self,
        tmp_path: Path,
    ) -> None:
        first_root = tmp_path / "first"
        second_root = tmp_path / "second"
        _write_module_config(first_root / "duplicate", name="duplicate")
        _write_module_config(second_root / "duplicate", name="duplicate")
        loader = DataLoader(input_dirs=[first_root, second_root])

        with pytest.raises(
            AmbiguousModuleConfigError,
            match="multiple config.yaml candidates",
        ):
            loader.get_initialized_config("duplicate")

    def test_get_initialized_config_circular_dependency(
        self, empty_data_loader: DataLoader
    ) -> None:
        root = KnowledgeBaseConfig(name="root", version="1.0.0", modules=["mod_a"])
        mod_a = KnowledgeBaseConfig(
            name="mod_a", version="1.0.0", depends_on=["mod_b"], modules=[]
        )
        mod_b = KnowledgeBaseConfig(
            name="mod_b", version="1.0.0", depends_on=["mod_a"], modules=[]
        )
        empty_data_loader.module_configs = {
            root.name: root,
            mod_a.name: mod_a,
            mod_b.name: mod_b,
        }

        with pytest.raises(ValueError, match="Circular dependency"):
            empty_data_loader.get_initialized_config("root")

    def test_get_initialized_config_empty_modules(
        self, empty_data_loader: DataLoader
    ) -> None:
        kb = KnowledgeBaseConfig(
            name="root", version="1.0.0", modules=[], depends_on=[]
        )
        empty_data_loader.module_configs = {
            kb.name: kb,
        }
        initialized_kb = empty_data_loader.get_initialized_config("root")
        assert initialized_kb.modules == []

    def test_collect_module_closure_traverses_dependencies_and_child_modules(
        self,
        empty_data_loader: DataLoader,
    ) -> None:
        mod_a = KnowledgeBaseConfig(
            name="mod_a", version="1.0.0", depends_on=["mod_b"], modules=[]
        )
        mod_b = KnowledgeBaseConfig(
            name="mod_b", version="1.0.0", depends_on=[], modules=["mod_c"]
        )
        mod_c = KnowledgeBaseConfig(name="mod_c", version="1.0.0", modules=[])
        empty_data_loader.module_configs = {
            mod_a.name: mod_a,
            mod_b.name: mod_b,
            mod_c.name: mod_c,
        }

        collected, preferred_order = empty_data_loader._collect_module_closure(  # type: ignore
            ["mod_a"]
        )
        assert set(collected.keys()) == {"mod_a", "mod_b", "mod_c"}
        assert preferred_order == ["mod_a", "mod_b", "mod_c"]

        collected, preferred_order = empty_data_loader._collect_module_closure(  # type:ignore
            ["mod_b", "mod_a"]
        )  # type: ignore
        assert set(collected.keys()) == {"mod_a", "mod_b", "mod_c"}
        assert preferred_order == ["mod_b", "mod_c", "mod_a"]

    def test_resolve_module_load_order(
        self,
    ) -> None:
        mod_a = KnowledgeBaseConfig(
            name="mod_a", version="1.0.0", depends_on=["mod_b"], modules=[]
        )
        mod_b = KnowledgeBaseConfig(
            name="mod_b", version="1.0.0", depends_on=["mod_c"], modules=[]
        )
        mod_c = KnowledgeBaseConfig(name="mod_c", version="1.0.0", modules=[])

        modules_dict = {
            mod_a.name: mod_a,
            mod_b.name: mod_b,
            mod_c.name: mod_c,
        }

        load_order = resolve_kb_module_load_order(
            modules=modules_dict,
            preferred_order=["mod_a", "mod_b", "mod_c"],
        )
        assert load_order == ["mod_c", "mod_b", "mod_a"]

        load_order = resolve_kb_module_load_order(
            modules=modules_dict,
            preferred_order=["mod_c", "mod_b", "mod_a"],
        )
        assert load_order == ["mod_c", "mod_b", "mod_a"]

    def test_get_initialized_default_kb(self, yaml_data_loader: DataLoader) -> None:
        kb_config = yaml_data_loader.get_initialized_config("lx_knowledge_base")

        assert kb_config.modules is not None

    def test_default_loader_uses_packaged_data_root(self) -> None:
        kb = DataLoader().load_knowledge_base("report_template_examples")

        assert kb.config.name == "report_template_examples"

    def test_explicit_input_dir_uses_supplied_path(self, tmp_path: Path) -> None:
        default_loader = DataLoader()
        default_loader.load_module_configs()
        default_config = default_loader.get_initialized_config("star_upper_gi")
        assert default_config.source_file is not None
        assert default_config.source_file.as_posix().endswith(
            "lx_dtypes/data/star_upper_gi/config.yaml"
        )

        explicit_root = tmp_path / "custom-loader-root"
        _write_minimal_module_config(
            explicit_root / "star_upper_gi",
            module_name="star_upper_gi",
        )
        explicit_loader = DataLoader(input_dirs=[explicit_root])
        kb = explicit_loader.load_knowledge_base("star_upper_gi")

        assert kb.config.name == "star_upper_gi"
        assert kb.config.source_file is not None
        assert kb.config.source_file.as_posix().endswith(
            "custom-loader-root/star_upper_gi/config.yaml"
        )

    def test_non_existing_input_dir_provided(self) -> None:
        loader = DataLoader(input_dirs=[Path("./non_existing_dir/")])
        config_files = loader.fetch_config_yamls()
        assert config_files == []

    def test_load_knowledge_base_prefers_bundle_scoped_module(
        self,
        tmp_path: Path,
    ) -> None:
        canonical_units_dir = tmp_path / "terminology" / "lx_units"
        _write_module_config(
            canonical_units_dir,
            name="lx_units",
            modules=[],
            depends_on=[],
            data_dirs=["./data"],
        )
        _write_unit(
            canonical_units_dir,
            name="canonical_centimeter",
            abbreviation="cm",
        )

        editor_bundle_dir = tmp_path / "editor_bundle"
        _write_module_config(
            editor_bundle_dir,
            name="editor_bundle",
            modules=["lx_units"],
            depends_on=[],
            data_dirs=[],
        )
        editor_units_dir = editor_bundle_dir / "lx_units"
        _write_module_config(
            editor_units_dir,
            name="lx_units",
            modules=[],
            depends_on=[],
            data_dirs=["./data"],
        )
        _write_unit(
            editor_units_dir,
            name="editor_millimeter",
            abbreviation="mm",
        )

        loader = DataLoader(input_dirs=[tmp_path])
        kb = loader.load_knowledge_base("editor_bundle")

        assert "editor_millimeter" in kb.unit
        assert "canonical_centimeter" not in kb.unit
