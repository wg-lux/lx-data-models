from pathlib import Path

from lx_dtypes.models.interface.KnowledgeBaseConfig import KnowledgeBaseConfig

MAIN_KNOWLEDGE_BASE_CONFIG_FILE_PATH = Path(
    "./lx_dtypes/data/sample_knowledge_base/config.yaml"
)


class TestKnowledgeBaseConfig:
    def test_creation_from_yaml(
        self, config_file_path: Path = MAIN_KNOWLEDGE_BASE_CONFIG_FILE_PATH
    ) -> None:
        kb_config = KnowledgeBaseConfig.from_yaml_file(config_file_path)

        assert kb_config.name == "lx_knowledge_base"
        assert isinstance(kb_config.depends_on, list)
        assert isinstance(kb_config.modules, list)

    def test_creation_from_yaml_preserves_medical_field(self, tmp_path: Path) -> None:
        config_path = tmp_path / "config.yaml"
        config_path.write_text(
            "\n".join(
                [
                    "name: gastro_bundle",
                    "description: ''",
                    "version: 2026.04.30",
                    "medical_field: gastroenterology",
                    "modules: []",
                    "depends_on: []",
                ]
            )
            + "\n"
        )

        kb_config = KnowledgeBaseConfig.from_yaml_file(config_path)

        assert kb_config.medical_field == "gastroenterology"

    def test_creation_from_yaml_preserves_author(self, tmp_path: Path) -> None:
        config_path = tmp_path / "config.yaml"
        config_path.write_text(
            "\n".join(
                [
                    "name: author_bundle",
                    "description: ''",
                    "version: 2026.05.04",
                    "medical_field: cardiology",
                    "author: Dr. Beispiel",
                    "modules: []",
                    "depends_on: []",
                ]
            )
            + "\n"
        )

        kb_config = KnowledgeBaseConfig.from_yaml_file(config_path)

        assert kb_config.medical_field == "cardiology"
        assert kb_config.author == "Dr. Beispiel"

    def test_creation_from_dataloader(
        self,
        uninitialized_demo_kb_config: KnowledgeBaseConfig,
    ) -> None:
        assert isinstance(uninitialized_demo_kb_config, KnowledgeBaseConfig)
        assert uninitialized_demo_kb_config.name == "lx_knowledge_base"
        assert isinstance(uninitialized_demo_kb_config.depends_on, list)
        assert isinstance(uninitialized_demo_kb_config.modules, list)

    def test_normalize_data_paths_no_config_file_error(
        self,
        uninitialized_demo_kb_config: KnowledgeBaseConfig,
    ) -> None:
        """
        Verify that calling `normalize_data_paths` with `config_file=None` raises a ValueError when no source file is set.

        This test sets both `kb_config.source_file` and `kb_config.data.source_file` to None and asserts that `normalize_data_paths(config_file=None)` raises a ValueError with the message "source_file must be set to normalize data paths".

        Parameters:
            uninitialized_demo_kb_config (KnowledgeBaseConfig): Fixture providing a base KnowledgeBaseConfig instance to copy and modify for the test.
        """
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

    # def test_reimport_sample_kb(self, )
