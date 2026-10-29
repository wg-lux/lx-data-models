"""Portable spaCy matcher rules and source-bound finding-presence evidence."""

from collections.abc import Mapping, Sequence
from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .json_types import JsonValue
from .knowledge_base import KnowledgeBaseIdentity

type FindingPresence = Literal["present", "absent", "uncertain"]


class FindingTextRule(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    presence: FindingPresence
    pattern: list[dict[str, JsonValue]] = Field(min_length=1, max_length=100)


class FindingMention(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    finding: str = Field(min_length=1)
    presence: FindingPresence
    start: int = Field(ge=0)
    end: int = Field(gt=0)

    @model_validator(mode="after")
    def ordered_span(self) -> "FindingMention":
        if self.end <= self.start:
            raise ValueError("Finding mention must have a nonempty character span")
        return self


class ClassificationTextRule(BaseModel):
    """Match a classification choice; hosts attach it only to a present finding."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    classification: str = Field(min_length=1, max_length=255)
    choice: str = Field(min_length=1, max_length=255)
    pattern: list[dict[str, JsonValue]] = Field(min_length=1, max_length=100)


class ClassificationMention(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    finding: str = Field(min_length=1)
    classification: str = Field(min_length=1)
    choice: str = Field(min_length=1)
    start: int = Field(ge=0)
    end: int = Field(gt=0)

    @model_validator(mode="after")
    def ordered_span(self) -> "ClassificationMention":
        if self.end <= self.start:
            raise ValueError(
                "Classification mention must have a nonempty character span"
            )
        return self


class FindingExtractionEvidence(KnowledgeBaseIdentity):
    source: Literal["anonymized_text"] = "anonymized_text"
    mentions: list[FindingMention]


class FindingTextExtractor(Protocol):
    def __call__(
        self, text: str, findings: Mapping[str, Sequence[FindingTextRule]]
    ) -> Sequence[FindingMention]: ...
