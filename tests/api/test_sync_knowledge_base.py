from typing import Callable

import pytest

from lx_dtypes.lx_django.parser.main import (
    sync_django_db_from_knowledge_base,
)
from lx_dtypes.models.base_models.log import Log
from lx_dtypes.models.knowledge_base import DataLoader, KnowledgeBase


@pytest.mark.django_db
class TestSyncKnowledgeBase:
    def test_sync_sample_knowledge_base(
        self,
        yaml_data_loader: DataLoader,
        lx_knowledge_base: KnowledgeBase,
        log_writer: Callable[..., Log],
    ) -> None:
        sync_django_db_from_knowledge_base(
            kb=lx_knowledge_base,
        )
