from pytest import fixture

from lx_dtypes.models.knowledge_base import DataLoader, KnowledgeBase


@fixture(scope="session")
def lx_knowledge_base(
    yaml_data_loader: DataLoader, demo_kb_config_name: str
) -> KnowledgeBase:
    kb = yaml_data_loader.load_knowledge_base(demo_kb_config_name)
    return kb
