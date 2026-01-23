import pytest

from ..DataLoader import DataLoader
from ..DbInterface import DbInterface
from ..KnowledgeBase import KnowledgeBase
from ..KnowledgeBaseConfig import KnowledgeBaseConfig
from ..Ledger import Ledger


@pytest.fixture(scope="session")
def ledger_fixture() -> "Ledger":
    """
    Create a session-scoped Ledger used by tests.

    Returns:
        ledger (Ledger): Ledger instance with UUID "423e4567-e89b-12d3-a456-426614174003" and tags ["ledger_tag1", "ledger_tag2"].
    """
    ledger = Ledger(
        uuid="423e4567-e89b-12d3-a456-426614174003",
        tags=["ledger_tag1", "ledger_tag2"],
    )
    return ledger


@pytest.fixture(scope="session")
def knowledge_base_fixture() -> "KnowledgeBase":
    """
    Create a KnowledgeBase instance preconfigured for tests.

    The returned KnowledgeBase has a predefined UUID and tags and is populated with a KnowledgeBaseConfig that includes name, localized names (de/en), description, UUID, tags, dependencies, modules, and version.

    Returns:
        KnowledgeBase: The configured KnowledgeBase instance.
    """
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
    """
    Load a KnowledgeBase from YAML using the provided data loader and configuration name.

    Parameters:
        yaml_data_loader (DataLoader): DataLoader instance used to load the knowledge base from YAML.
        demo_kb_config_name (str): Name or identifier of the knowledge-base configuration to load.

    Returns:
        KnowledgeBase: The loaded KnowledgeBase instance corresponding to the given configuration name.
    """
    kb = yaml_data_loader.load_knowledge_base(demo_kb_config_name)
    return kb


@pytest.fixture(scope="session")
def db_interface_fixture(
    lx_knowledge_base: "KnowledgeBase",
    ledger_fixture: "Ledger",
) -> "DbInterface":
    """
    Create a DbInterface instance linking a knowledge base and a ledger for tests.

    Parameters:
        lx_knowledge_base (KnowledgeBase): The knowledge base to attach to the interface.
        ledger_fixture (Ledger): The ledger to attach to the interface.

    Returns:
        DbInterface: A DbInterface configured with the provided knowledge base and ledger, and preset UUID and tags for test use.
    """
    interface = DbInterface(
        uuid="123e4567-e89b-12d3-a456-426614174000",
        tags=["interface_tag1", "interface_tag2"],
        knowledge_base=lx_knowledge_base,
        ledger=ledger_fixture,
    )
    return interface
