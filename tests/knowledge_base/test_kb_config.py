from pathlib import Path

from lx_dtypes.models import KnowledgeBaseConfig

MAIN_KNOWLEDGE_BASE_CONFIG_FILE_PATH = Path("./lx_dtypes/data/sample_knowledge_base/config.yaml")


class TestKnowledgeBaseConfig:
    def test_creation_from_yaml(self, config_file_path: Path = MAIN_KNOWLEDGE_BASE_CONFIG_FILE_PATH):
        kb_config = KnowledgeBaseConfig.from_yaml_file(config_file_path)

        assert kb_config.name == "lx_knowledge_base"
        assert kb_config.name_de == "lx_knowledge_base"
        assert kb_config.name_en == "lx_knowledge_base"
        assert isinstance(kb_config.depends_on, list)
        assert isinstance(kb_config.modules, list)

    def test_creation_from_dataloader(
        self,
        uninitialized_demo_kb_config: KnowledgeBaseConfig,
    ):
        assert isinstance(uninitialized_demo_kb_config, KnowledgeBaseConfig)
        assert uninitialized_demo_kb_config.name == "lx_knowledge_base"
        assert isinstance(uninitialized_demo_kb_config.depends_on, list)
        assert isinstance(uninitialized_demo_kb_config.modules, list)

    def test_normalize_data_paths_no_config_file_error(
        self,
        uninitialized_demo_kb_config: KnowledgeBaseConfig,
    ):
        kb_config = uninitialized_demo_kb_config.model_copy(deep=True)
        kb_config.source_file = None
        kb_config.data.source_file = None

        # kb_config.normalize_data_paths(config_file=None) should raise ValueError
        try:
            kb_config.normalize_data_paths(config_file=None)
        except ValueError as e:
            assert str(e) == "source_file must be set to normalize data paths"
        else:
            assert False, "Expected ValueError was not raised"
