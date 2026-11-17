"""Named time relationships and portable reference/training examples."""

from typing import Self, TypedDict

from pydantic import Field, model_validator

from lx_dtypes.models.base.app_base_model.ddict.KnowledgebaseBaseModelDataDict import (
    KnowledgebaseBaseModelDataDict,
)
from lx_dtypes.models.base.app_base_model.pydantic.KnowledgebaseBaseModel import (
    KnowledgebaseBaseModel,
)
from lx_dtypes.models.contracts.json_types import JsonObject
from lx_dtypes.models.contracts.time_reference import (
    TimeOffsetEvidence,
    TimeOffsetExample,
    TimestampKind,
)
from lx_dtypes.models.contracts.validation import SemanticValidationError


class TimeReferenceDataDict(KnowledgebaseBaseModelDataDict):
    reference_kind: TimestampKind
    target_kind: TimestampKind
    examples: list[JsonObject]


class TimeReference(KnowledgebaseBaseModel[TimeReferenceDataDict]):
    name: str = Field(min_length=1, max_length=255)
    reference_kind: TimestampKind = "pts"
    target_kind: TimestampKind = "electrosurgery"
    examples: list[TimeOffsetExample] = Field(default_factory=list)

    def validate_evidence(self, evidence: TimeOffsetEvidence) -> None:
        evidence = TimeOffsetEvidence.model_validate(evidence)
        if (evidence.offset.reference.kind, evidence.offset.target.kind) != (
            self.reference_kind,
            self.target_kind,
        ):
            raise SemanticValidationError(
                "terminology.time_reference_kind_mismatch",
                "Time evidence clock kinds disagree with the KB definition",
            )

    @model_validator(mode="after")
    def validate_examples(self) -> Self:
        identifiers = [example.example_id for example in self.examples]
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("Time example IDs must be unique within a definition")
        for example in self.examples:
            self.validate_evidence(example.evidence)
        return self

    @property
    def ddict_class(self) -> type[TimeReferenceDataDict]:
        return TimeReferenceDataDict


class KbTimeReferenceLookupType(TypedDict):
    TimeReference: type[TimeReference]
