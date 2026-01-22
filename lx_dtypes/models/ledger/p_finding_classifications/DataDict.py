from typing import List

from lx_dtypes.models.base.app_base_model.ddict.LedgerBaseModelDataDict import (
    LedgerBaseModelDataDict,
)
from lx_dtypes.models.ledger.p_finding_classification_choice.DataDict import (
    PFindingClassificationChoiceDataDict,
)


class PFindingClassificationsDataDict(LedgerBaseModelDataDict):
    patient_finding: str
    patient_finding_classification_choices: List[PFindingClassificationChoiceDataDict]


class SerializedPFindingClassificationsDataDict(LedgerBaseModelDataDict):
    patient_finding: str
    patient_finding_classification_choices: str
