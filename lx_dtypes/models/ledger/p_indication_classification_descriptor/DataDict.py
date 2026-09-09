from lx_dtypes.models.base.app_base_model.ddict.LedgerBaseModelDataDict import (
    LedgerBaseModelDataDict,
)
from lx_dtypes.models.descriptor_value import DescriptorValue


class PIndicationClassificationDescriptorDataDict(LedgerBaseModelDataDict):
    patient_indication_classification: str
    classification_choice_descriptor: str
    descriptor_value: DescriptorValue
