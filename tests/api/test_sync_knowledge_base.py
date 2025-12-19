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
        kb_config = kb.config_safe

        for module in kb_config.modules:
            log_writer(module)
