from typing import Any

from lx_dtypes.models.interface.KnowledgeBase import (
    KnowledgeBase,
    SemanticAdmissibilityError,
)
from lx_dtypes.models.interface.KnowledgeBaseAdmissibility import (
    SemanticAdmissibilityError as AdapterAdmissibilityError,
)
from lx_dtypes.models.knowledge_base.report_template.ReportTemplate import (
    ReportTemplate,
)

# from ..KnowledgeBaseConfig import KnowledgeBaseConfig


class TestKnowledgeBaseFixture:
    def test_knowledge_base_fixture(
        self,
        knowledge_base_fixture: "KnowledgeBase",
    ) -> None:
        assert knowledge_base_fixture.config.name == "Knowledge Base Name"


def test_admissibility_error_keeps_its_public_identity() -> None:
    assert SemanticAdmissibilityError is AdapterAdmissibilityError


def test_reporting_delegation_preserves_overrides_and_live_kb_state(
    knowledge_base_fixture: KnowledgeBase,
) -> None:
    class CustomKnowledgeBase(KnowledgeBase):
        def export_report_template(self, name: str) -> dict[str, Any]:
            return {"name": self.get_report_template(name).name}

    kb = CustomKnowledgeBase.model_validate(knowledge_base_fixture.model_dump())
    before = kb.model_dump()
    assert kb.export_report_templates() == []
    assert kb.model_dump() == before
    kb.report_template["new_template"] = ReportTemplate(
        name="new_template", examination="demo_exam"
    )
    before = kb.model_dump()
    assert kb.export_report_templates() == [{"name": "new_template"}]
    assert kb.model_dump() == before
