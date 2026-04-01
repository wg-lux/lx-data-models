from lx_dtypes.models.base.app_base_model.ddict.LedgerBaseModelDataDict import (
    LedgerBaseModelDataDict,
)
from lx_dtypes.models.ledger.p_indication_classification_descriptor.DataDict import (
    PIndicationClassificationDescriptorDataDict,
)


class PIndicationClassificationDataDict(LedgerBaseModelDataDict):
    patient_indication: str
    classification_choice: str
    classification: str
    patient_indication_classification_descriptors: list[
        PIndicationClassificationDescriptorDataDict
    ]


class SerializedPIndicationClassificationDataDict(LedgerBaseModelDataDict):
    patient_indication: str
    classification_choice: str
    classification: str
    patient_indication_classification_descriptors: str
