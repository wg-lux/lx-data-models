"""Typed dictionary transport for ledger observations."""

from datetime import datetime

from lx_dtypes.models.base.app_base_model.ddict.LedgerBaseModelDataDict import (
    LedgerBaseModelDataDict,
)
from lx_dtypes.models.contracts.json_types import JsonObject


class PElectricalApplicationDataDict(LedgerBaseModelDataDict):
    patient_examination: str
    electrical_curve_profile: str
    knowledge_base_module: str
    knowledge_base_version: str
    measurement_source_sha256: str
    session_id: str
    clock_id: str
    time_base_num: int
    time_base_den: int
    sample_start_index: int
    sample_end_index: int
    start_timestamp: int
    end_timestamp: int
    started_at: datetime
    curve: JsonObject


class PElectricalCurveComparisonDataDict(LedgerBaseModelDataDict):
    patient_examination: str
    electrical_curve_profile: str
    knowledge_base_module: str
    knowledge_base_version: str
    algorithm: str
    application: str
    reference_applications: list[str]
    result: JsonObject
