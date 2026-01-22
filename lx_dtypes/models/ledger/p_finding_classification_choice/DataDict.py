from lx_dtypes.models.base.app_base_model.ddict.LedgerBaseModelDataDict import (
    LedgerBaseModelDataDict,
)
from lx_dtypes.models.ledger.p_finding_classification_choice_descriptor.DataDict import (
    PFindingClassificationChoiceDescriptorDataDict,
)


class PFindingClassificationChoiceDataDict(LedgerBaseModelDataDict):
    patient_finding_classifications: str
    classification_choice: str
    classification: str
    patient_finding_classification_choice_descriptors: list[
        PFindingClassificationChoiceDescriptorDataDict
    ]


class SerializedPFindingClassificationChoiceDataDict(LedgerBaseModelDataDict):
    patient_finding_classifications: str
    classification_choice: str
    classification: str
    patient_finding_classification_choice_descriptors: str
