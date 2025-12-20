from typing import Callable

import pytest

from lx_dtypes.models.base_models.log import Log
from lx_dtypes.models.knowledge_base import DataLoader, KnowledgeBase


# TODO add transform utils based on those tests
@pytest.mark.django_db
class TestSyncKnowledgeBase:
    def test_get_dependency_graph(
        self,
        yaml_data_loader: DataLoader,
        lx_knowledge_base: KnowledgeBase,
        log_writer: Callable[..., Log],
    ) -> None:
        kb = lx_knowledge_base
        kb_entries_by_module_name = kb.kb_entries_by_module_name()

        kb_config = kb.config
        assert kb_config is not None

        ordered_module_names = kb_config.modules

        for module_name in ordered_module_names:
            assert module_name in kb_entries_by_module_name
            #

        # for module_name, entries in kb_entries_by_module_name.items():
        #     log_writer(
        #         f"Module '{module_name}' has {len(entries)} entries.",
        #         context={"module_name": module_name, "entry_count": str(len(entries))},
        #     )
