from typing import Dict

from lx_dtypes.models.base.app_base_model.ddict.LedgerBaseModelDataDict import (
    LedgerBaseModelDataDict,
)
from lx_dtypes.models.base.file.patient_file_mixin import (
    PatientFileMixInDataDict,
    SerializedPatientFileMixInDataDict,
)
from lx_dtypes.models.ledger.p_video_segment.DataDict import PVideoSegmentDataDict
from lx_dtypes.models.meta.SensitiveMeta import (
    SensitiveMetaDataDict,
)

from .state import AnonymizationState


class PatientVideoFileDataDict(PatientFileMixInDataDict, LedgerBaseModelDataDict):
    anonymization_state: AnonymizationState
    sensitive_meta: SensitiveMetaDataDict
    patient_video_segments: Dict[str, "PVideoSegmentDataDict"]


class SerializedPatientVideoFileDataDict(
    SerializedPatientFileMixInDataDict, LedgerBaseModelDataDict
):
    anonymization_state: AnonymizationState
