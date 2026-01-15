from typing import Dict

from pydantic import Field

# from lx_dtypes.factories.typed_dicts
from lx_dtypes.models.base.app_base_model.ddict.AppBaseModelUUIDTagsDataDict import (
    AppBaseModelUUIDTagsDataDict,
)
from lx_dtypes.models.base.app_base_model.pydantic.AppBaseModelUUIDTags import (
    AppBaseModelUUIDTags,
)
from lx_dtypes.models.ledger.center import Center, CenterDataDict
from lx_dtypes.models.ledger.p_examination import PExamination, PExaminationDataDict
from lx_dtypes.models.ledger.patient import Patient, PatientDataDict


class LedgerDataDict(AppBaseModelUUIDTagsDataDict):
    patient_examinations: Dict[str, PExaminationDataDict]
    patients: Dict[str, PatientDataDict]
    centers: Dict[str, CenterDataDict]


class Ledger(AppBaseModelUUIDTags):
    patient_examinations: Dict[str, PExamination] = Field(default_factory=dict)
    patients: Dict[str, Patient] = Field(default_factory=dict)
    centers: Dict[str, Center] = Field(default_factory=dict)
