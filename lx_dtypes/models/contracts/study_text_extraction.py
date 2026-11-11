"""Cohort-scoped report text evidence, review suggestions and explicit approval."""

from typing import Literal
from uuid import UUID

from pydantic import Field

from lx_dtypes.models.model import FrozenContractModel, StrictContractModel

from .finding_extraction import ClassificationMention, FindingMention, FindingPresence
from .knowledge_base import KnowledgeBaseIdentity


class StudyTextExtractionEvidence(KnowledgeBaseIdentity):
    """Matches of one saved cohort definition against one anonymized report."""

    source: Literal["anonymized_text"] = "anonymized_text"
    cohort_definition_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    mentions: list[FindingMention]
    classification_mentions: list[ClassificationMention] = Field(
        default_factory=list[ClassificationMention]
    )


class StudyClassificationSuggestion(FrozenContractModel):
    classification: str = Field(min_length=1)
    choice: str = Field(min_length=1)
    title: str = Field(min_length=1)
    evidence: list[str]


class StudyFindingSuggestion(StrictContractModel):
    report: int = Field(gt=0)
    examination: int = Field(gt=0)
    finding: str = Field(min_length=1)
    title: str = Field(min_length=1)
    presence: FindingPresence
    evidence: list[str]
    classifications: list[StudyClassificationSuggestion] = Field(
        default_factory=list[StudyClassificationSuggestion]
    )
    # JSON transports UUIDs as strings.
    instance: UUID = Field(strict=False)
    approved: bool = False


class StudyClassificationSelection(FrozenContractModel):
    classification: str = Field(min_length=1)
    choice: str = Field(min_length=1)


class StudyFindingApprovalRequest(StrictContractModel):
    """Approve one recomputed suggestion with a subset of its classifications."""

    report: int = Field(gt=0)
    # JSON transports UUIDs as strings.
    instance: UUID = Field(strict=False)
    classifications: list[StudyClassificationSelection] = Field(
        default_factory=list[StudyClassificationSelection], max_length=100
    )
