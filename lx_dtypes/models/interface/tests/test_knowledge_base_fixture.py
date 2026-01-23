from ..KnowledgeBase import KnowledgeBase

# from ..KnowledgeBaseConfig import KnowledgeBaseConfig


class TestKnowledgeBaseFixture:
    def test_knowledge_base_fixture(
        self,
        knowledge_base_fixture: "KnowledgeBase",
    ) -> None:
        assert knowledge_base_fixture.config.name == "Knowledge Base Name"
