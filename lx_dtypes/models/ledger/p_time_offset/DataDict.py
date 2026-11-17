"""Typed dictionary transport for ledger observations."""

from lx_dtypes.models.base.app_base_model.ddict.LedgerBaseModelDataDict import (
    LedgerBaseModelDataDict,
)
from lx_dtypes.models.contracts.json_types import JsonObject


class PTimeOffsetDataDict(LedgerBaseModelDataDict):
    patient_examination: str
    time_reference: str
    knowledge_base_module: str
    knowledge_base_version: str
    evidence: JsonObject
