from pathlib import Path

import pytest

from lx_dtypes.models import KnowledgeBaseConfig
from lx_dtypes.models.knowledge_base import DataLoader
from lx_dtypes.utils.dataloader import resolve_kb_module_load_order


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

        with pytest.raises(ValueError, match="referenced but no configuration"):
            empty_data_loader.get_initialized_config("root")

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

    def test_collect_modules_with_dependencies(
        self,
        empty_data_loader: DataLoader,
    ) -> None:
        mod_a = KnowledgeBaseConfig(
            name="mod_a", version="1.0.0", depends_on=["mod_b"], modules=[]
        )
        mod_b = KnowledgeBaseConfig(
            name="mod_b", version="1.0.0", depends_on=["mod_c"], modules=[]
        )
        mod_c = KnowledgeBaseConfig(name="mod_c", version="1.0.0", modules=[])
        empty_data_loader.module_configs = {
            mod_a.name: mod_a,
            mod_b.name: mod_b,
            mod_c.name: mod_c,
        }

        collected = empty_data_loader._collect_modules_with_dependencies(["mod_a"])  # type: ignore
        assert set(collected.keys()) == {"mod_a", "mod_b", "mod_c"}

        collected = empty_data_loader._collect_modules_with_dependencies(  # type:ignore
            ["mod_b", "mod_a"]
        )  # type: ignore
        assert set(collected.keys()) == {"mod_a", "mod_b", "mod_c"}

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

    def test_non_existing_input_dir_provided(self) -> None:
        loader = DataLoader(input_dirs=[Path("./non_existing_dir/")])
        config_files = loader.fetch_config_yamls()
        assert config_files == []
