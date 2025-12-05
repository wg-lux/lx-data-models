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
