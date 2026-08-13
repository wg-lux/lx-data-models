from pathlib import Path

import pytest
from pydantic import ValidationError

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

    def test_exposes_canonical_contract_identity(
        self,
        uninitialized_demo_kb_config: KnowledgeBaseConfig,
    ) -> None:
        identity = uninitialized_demo_kb_config.knowledge_base_identity

        assert identity.knowledge_base_module == "lx_knowledge_base"
        assert identity.knowledge_base_version == "0.1.0"
        assert identity.canonical_name == "lx_knowledge_base@0.1.0"

    @pytest.mark.parametrize(
        ("field_name", "value"),
        [
            ("modules", ["child", "child"]),
            ("depends_on", [""]),
            ("modules", ["root"]),
        ],
    )
    def test_rejects_ambiguous_module_graph_entries(
        self, field_name: str, value: list[str]
    ) -> None:
        payload = {
            "name": "root",
            "version": "1.0.0",
            "modules": [],
            "depends_on": [],
        }
        payload[field_name] = value

        with pytest.raises(ValidationError):
            KnowledgeBaseConfig.model_validate(payload)

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

    def test_normalize_data_paths_uses_config_parent_as_base(
        self, tmp_path: Path
    ) -> None:
        module_dir = tmp_path / "star_upper_gi"
        (module_dir / "data").mkdir(parents=True)
        (module_dir / "relative").mkdir(parents=True)
        (module_dir / "data" / "units.yaml").write_text("- model: unit\n  name: demo\n")
        (module_dir / "relative" / "manifest.yaml").write_text("name: demo-manifest\n")
        (module_dir / "schema.yaml").write_text("schema: demo\n")

        config_path = module_dir / "config.yaml"
        config_path.write_text(
            "\n".join(
                [
                    "name: star_upper_gi",
                    'description: ""',
                    "version: 0.1.0",
                    "modules: []",
                    "depends_on: []",
                    "data:",
                    "  file: ./schema.yaml",
                    "  dirs:",
                    "    - ./data",
                    "  files:",
                    "    - ./relative/manifest.yaml",
                ]
            )
            + "\n"
        )

        kb_config = KnowledgeBaseConfig.from_yaml_file(config_path)
        kb_config.normalize_data_paths(config_path)

        assert kb_config.data.file == (module_dir / "schema.yaml").resolve()
        assert kb_config.data.dirs == [(module_dir / "data").resolve()]
        assert kb_config.data.files == [
            (module_dir / "relative" / "manifest.yaml").resolve()
        ]

    # def test_reimport_sample_kb(self, )
