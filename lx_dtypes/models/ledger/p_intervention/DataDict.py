from lx_dtypes.models.base.app_base_model.ddict.LedgerBaseModelDataDict import (
    LedgerBaseModelDataDict,
)


class PFindingInterventionDataDict(LedgerBaseModelDataDict):
    intervention: str
    patient_finding_interventions: str
