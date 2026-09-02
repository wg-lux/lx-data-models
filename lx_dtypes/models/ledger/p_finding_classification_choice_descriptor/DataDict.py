from lx_dtypes.models.base.app_base_model.ddict.LedgerBaseModelDataDict import (
    LedgerBaseModelDataDict,
)
from lx_dtypes.models.descriptor_value import DescriptorValue


class PFindingClassificationChoiceDescriptorDataDict(LedgerBaseModelDataDict):
    patient_finding_classification_choice: str
    classification_choice_descriptor: str
    descriptor_value: DescriptorValue
