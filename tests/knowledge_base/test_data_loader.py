import pytest

from lx_dtypes.models import KnowledgeBaseConfig
from lx_dtypes.models.knowledge_base import DataLoader


@pytest.fixture
def empty_data_loader() -> DataLoader:
    return DataLoader(input_dirs=[])


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

    def test_initialized_config_orders_dependencies(
        self,
        yaml_data_loader: DataLoader,
    ) -> None:
        kb_config = yaml_data_loader.get_initialized_config("lx_knowledge_base")

        assert isinstance(kb_config.modules, list)
        assert kb_config.modules == [
            "information_source_data",
            "lx_utils",
            "lx_hardware",
            "example_terminology",
        ]

    def test_get_initialized_config_missing_module(self, empty_data_loader: DataLoader) -> None:
        with pytest.raises(ValueError, match="is not loaded"):
            empty_data_loader.get_initialized_config("unknown")

    def test_get_initialized_config_missing_dependency(self, empty_data_loader: DataLoader) -> None:
        root = KnowledgeBaseConfig(name="root", version="1.0.0", modules=["mod_a"])
        mod_a = KnowledgeBaseConfig(name="mod_a", version="1.0.0", depends_on=["ghost"], modules=[])
        empty_data_loader.module_configs = {
            root.name: root,
            mod_a.name: mod_a,
        }

        with pytest.raises(ValueError, match="referenced but no configuration"):
            empty_data_loader.get_initialized_config("root")

    def test_get_initialized_config_circular_dependency(self, empty_data_loader: DataLoader) -> None:
        root = KnowledgeBaseConfig(name="root", version="1.0.0", modules=["mod_a"])
        mod_a = KnowledgeBaseConfig(name="mod_a", version="1.0.0", depends_on=["mod_b"], modules=[])
        mod_b = KnowledgeBaseConfig(name="mod_b", version="1.0.0", depends_on=["mod_a"], modules=[])
        empty_data_loader.module_configs = {
            root.name: root,
            mod_a.name: mod_a,
            mod_b.name: mod_b,
        }

        with pytest.raises(ValueError, match="Circular dependency"):
            empty_data_loader.get_initialized_config("root")
