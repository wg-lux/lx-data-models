from pytest import fixture

from lx_dtypes.lx_django.parser.main import (
    sync_django_db_from_knowledge_base,
)
from lx_dtypes.models.knowledge_base import DataLoader, KnowledgeBase


@fixture(scope="session")
def lx_knowledge_base(
    yaml_data_loader: DataLoader, demo_kb_config_name: str
) -> KnowledgeBase:
    kb = yaml_data_loader.load_knowledge_base(demo_kb_config_name)
    return kb


@fixture(scope="function")
def django_lx_knowledge_base(
    lx_knowledge_base: KnowledgeBase,
) -> None:
    sync_django_db_from_knowledge_base(
        kb=lx_knowledge_base,
    )
