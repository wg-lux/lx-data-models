import pytest

from ..DataLoader import DataLoader
from ..DbInterface import DbInterface
from ..KnowledgeBase import KnowledgeBase
from ..KnowledgeBaseConfig import KnowledgeBaseConfig
from ..Ledger import Ledger


@pytest.fixture(scope="session")
def ledger_fixture() -> "Ledger":
    ledger = Ledger(
        uuid="423e4567-e89b-12d3-a456-426614174003",
        tags=["ledger_tag1", "ledger_tag2"],
    )
    return ledger


@pytest.fixture(scope="session")
def knowledge_base_fixture() -> "KnowledgeBase":
    kb_config = KnowledgeBaseConfig(
        name="Knowledge Base Name",
        name_de="Wissensdatenbank Name",
        name_en="Knowledge Base Name EN",
        description="This is a knowledge base description.",
        uuid="223e4567-e89b-12d3-a456-426614174001",
        tags=["kb_tag1", "kb_tag2"],
        depends_on=["dependency1", "dependency2"],
        modules=["module1", "module2"],
        version="1.0.0",
    )
    knowledge_base = KnowledgeBase(
        uuid="323e4567-e89b-12d3-a456-426614174002",
        tags=["knowledge_base_tag1", "knowledge_base_tag2"],
        config=kb_config,
    )
    return knowledge_base


@pytest.fixture(scope="session")
def lx_knowledge_base(
    yaml_data_loader: DataLoader, demo_kb_config_name: str
) -> KnowledgeBase:
    kb = yaml_data_loader.load_knowledge_base(demo_kb_config_name)
    return kb


@pytest.fixture(scope="session")
def db_interface_fixture(
    lx_knowledge_base: "KnowledgeBase",
    ledger_fixture: "Ledger",
) -> "DbInterface":
    interface = DbInterface(
        uuid="123e4567-e89b-12d3-a456-426614174000",
        tags=["interface_tag1", "interface_tag2"],
        knowledge_base=lx_knowledge_base,
        ledger=ledger_fixture,
    )
    return interface
