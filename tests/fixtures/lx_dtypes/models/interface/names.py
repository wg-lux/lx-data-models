from pytest import fixture

SAMPLE_KNOWLEDGE_BASE_NAME = "lx_knowledge_base"


@fixture(scope="session")
def demo_kb_config_name() -> str:
    """
    Provide the sample knowledge base name used by tests.

    Returns:
        str: The sample knowledge base name "lx_knowledge_base".
    """
    return SAMPLE_KNOWLEDGE_BASE_NAME
