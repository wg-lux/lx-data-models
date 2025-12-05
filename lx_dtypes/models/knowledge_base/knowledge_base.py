from typing import TYPE_CHECKING, Dict, Optional

from pydantic import Field

if TYPE_CHECKING:
    from lx_dtypes.models.knowledge_base.knowledge_base_config import KnowledgeBaseConfig

from lx_dtypes.models.shallow import (
    ClassificationChoiceShallow,
    ClassificationShallow,
    ClassificationTypeShallow,
    ExaminationShallow,
    ExaminationTypeShallow,
    FindingShallow,
    FindingTypeShallow,
    IndicationShallow,
    IndicationTypeShallow,
)
from lx_dtypes.utils.mixins import BaseModelMixin


class KnowledgeBase(BaseModelMixin):
    """
    Model representing a knowledge base.

    """

    config: Optional["KnowledgeBaseConfig"] = None

    findings: Dict[str, "FindingShallow"] = Field(default_factory=dict)
    finding_types: Dict[str, "FindingTypeShallow"] = Field(default_factory=dict)
    classifications: Dict[str, "ClassificationShallow"] = Field(default_factory=dict)
    classification_types: Dict[str, "ClassificationTypeShallow"] = Field(default_factory=dict)
    classification_choices: Dict[str, "ClassificationChoiceShallow"] = Field(default_factory=dict)
    examinations: Dict[str, "ExaminationShallow"] = Field(default_factory=dict)
    examination_types: Dict[str, "ExaminationTypeShallow"] = Field(default_factory=dict)
    indications: Dict[str, "IndicationShallow"] = Field(default_factory=dict)
    indication_types: Dict[str, "IndicationTypeShallow"] = Field(default_factory=dict)

    def import_knowledge_base(self, other: "KnowledgeBase") -> None:
        """Merge another KnowledgeBase into this one.

        Args:
            other (KnowledgeBase): The other KnowledgeBase to merge.
        """
        self.findings.update(other.findings)
        self.finding_types.update(other.finding_types)
        self.classifications.update(other.classifications)
        self.classification_types.update(other.classification_types)
        self.classification_choices.update(other.classification_choices)
        self.examinations.update(other.examinations)
        self.examination_types.update(other.examination_types)
        self.indications.update(other.indications)
        self.indication_types.update(other.indication_types)
