"""Validated ledger observations and their KB identity checks."""

from pydantic import Field

from lx_dtypes.models.base.app_base_model.pydantic.LedgerBaseModel import (
    LedgerBaseModel,
)
from lx_dtypes.models.contracts.knowledge_base import KnowledgeBaseIdentity
from lx_dtypes.models.contracts.time_reference import TimeOffsetEvidence
from lx_dtypes.models.knowledge_base.time_reference import TimeReference
from lx_dtypes.models.ledger.kb_reference import ensure_pinned_definition

from .DataDict import PTimeOffsetDataDict


class PTimeOffset(LedgerBaseModel[PTimeOffsetDataDict]):
    patient_examination: str = Field(min_length=1)
    time_reference: str = Field(min_length=1)
    knowledge_base_module: str = Field(min_length=1, pattern=r"^[^@]+$")
    knowledge_base_version: str = Field(min_length=1, pattern=r"^[^@]+$")
    evidence: TimeOffsetEvidence

    def validate_reference(
        self, reference: TimeReference, identity: KnowledgeBaseIdentity
    ) -> None:
        ensure_pinned_definition(
            name=self.time_reference,
            module=self.knowledge_base_module,
            version=self.knowledge_base_version,
            definition=reference,
            identity=identity,
            label="Time observation",
        )
        reference.validate_evidence(self.evidence)

    @property
    def ddict_class(self) -> type[PTimeOffsetDataDict]:
        return PTimeOffsetDataDict

    @classmethod
    def nested_fields(cls) -> list[str]:
        return []
