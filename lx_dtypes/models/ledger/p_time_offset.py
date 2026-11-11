"""Examination-specific time observations linked to versioned KB definitions."""

from typing import TypedDict

from pydantic import Field

from lx_dtypes.models.base.app_base_model.ddict.LedgerBaseModelDataDict import (
    LedgerBaseModelDataDict,
)
from lx_dtypes.models.base.app_base_model.pydantic.LedgerBaseModel import (
    LedgerBaseModel,
)
from lx_dtypes.models.contracts.json_types import JsonObject
from lx_dtypes.models.contracts.knowledge_base import KnowledgeBaseIdentity
from lx_dtypes.models.contracts.time_reference import TimeOffsetEvidence
from lx_dtypes.models.contracts.validation import SemanticValidationError
from lx_dtypes.models.knowledge_base.time_reference import TimeReference


class PTimeOffsetDataDict(LedgerBaseModelDataDict):
    patient_examination: str
    time_reference: str
    knowledge_base_module: str
    knowledge_base_version: str
    evidence: JsonObject


class PTimeOffset(LedgerBaseModel[PTimeOffsetDataDict]):
    patient_examination: str = Field(min_length=1)
    time_reference: str = Field(min_length=1)
    knowledge_base_module: str = Field(min_length=1, pattern=r"^[^@]+$")
    knowledge_base_version: str = Field(min_length=1, pattern=r"^[^@]+$")
    evidence: TimeOffsetEvidence

    def validate_reference(
        self, reference: TimeReference, identity: KnowledgeBaseIdentity
    ) -> None:
        if self.time_reference != reference.name or (
            self.knowledge_base_module != reference.kb_module_name
            or self.knowledge_base_module != identity.knowledge_base_module
            or self.knowledge_base_version != identity.knowledge_base_version
        ):
            raise SemanticValidationError(
                "terminology.identity_mismatch",
                "Time observation must match its exact KB reference identity",
            )
        reference.validate_evidence(self.evidence)

    @property
    def ddict_class(self) -> type[PTimeOffsetDataDict]:
        return PTimeOffsetDataDict

    @classmethod
    def nested_fields(cls) -> list[str]:
        return []


class LPTimeOffsetLookupType(TypedDict):
    PTimeOffset: type[PTimeOffset]
