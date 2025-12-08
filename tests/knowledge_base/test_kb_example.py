from typing import Callable

from lx_dtypes.models.knowledge_base.knowledge_base import KnowledgeBase
from lx_dtypes.utils.logging import Log


class TestKnowledgeBaseModel:
    def test_load_default_kb(self, lx_knowledge_base: KnowledgeBase, log_writer: Callable[..., Log]):
        kb = lx_knowledge_base

        # TODO REMOVE LATER
        # Dump loaded KB to YAML for inspection
        # output_path = Path("./loaded_kb_dump.yaml")
        # dumped_model = kb.model_dump(mode="json")  # , exclude_defaults=True, exclude_none=True, exclude_unset=True)
        # with output_path.open("w", encoding="utf-8") as f:
        #     yaml.safe_dump(dumped_model, f, sort_keys=False, indent=2)

        assert len(kb.citations) > 0
        assert len(kb.information_sources) > 0
        assert len(kb.examinations) > 0
        assert len(kb.examination_types) > 0
        assert len(kb.indications) > 0
        assert len(kb.indication_types) > 0
        assert len(kb.findings) > 0
        assert len(kb.finding_types) > 0
        assert len(kb.classifications) > 0
        assert len(kb.classification_types) > 0
        assert len(kb.classification_choices) > 0
        assert len(kb.interventions) > 0
        assert len(kb.intervention_types) > 0

        counts = kb.count_entries()

        log_str = "".join([f"{key}: {value}" for key, value in counts.items()])
        log_writer(
            message="Loaded knowledge base entry counts:\n" + log_str,
        )
