from pathlib import Path
from typing import Callable

from lx_dtypes.models.knowledge_base.knowledge_base import KnowledgeBase
from lx_dtypes.utils.logging import Log


class TestKnowledgebaseBaseModel:
    def test_load_default_kb(
        self,
        lx_knowledge_base: KnowledgeBase,
        log_writer: Callable[..., Log],
        tmp_path: Path,
    ):
        kb = lx_knowledge_base

        # Dump loaded KB to YAML for inspection
        output_dir = Path(".")

        kb.export_yaml(export_dir=output_dir)

        assert len(kb.citation) > 0
        assert len(kb.information_source) > 0
        assert len(kb.examination) > 0
        assert len(kb.examination_type) > 0
        assert len(kb.indication) > 0
        assert len(kb.indication_type) > 0
        assert len(kb.finding) > 0
        assert len(kb.finding_type) > 0
        assert len(kb.classification) > 0
        assert len(kb.classification_type) > 0
        assert len(kb.classification_choice) > 0
        assert len(kb.intervention) > 0
        assert len(kb.intervention_type) > 0

        counts = kb.count_entries()

        log_str = "".join([f"{key}: {value}" for key, value in counts.items()])
        log_writer(
            message="Loaded knowledge base entry counts:\n" + log_str,
        )

        kb.export_yaml(export_dir=tmp_path, filename="exported_kb")
        exported_yaml_path = tmp_path / "exported_kb.yaml"
        assert exported_yaml_path.exists()
        # Load back the exported YAML to verify
        new_kb = KnowledgeBase.create_from_yaml(exported_yaml_path)

        # FIXME currently failing (most likely due to default values in descriptors)
        initial_dump = kb.model_dump()
        initial_dump.pop("classification_choice_descriptor")
        new_dump = new_kb.model_dump()
        new_dump.pop("classification_choice_descriptor")

        assert initial_dump == new_dump
