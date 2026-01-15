from typing import List, Union

from lx_dtypes.models.base.app_base_model.ddict.LedgerBaseModelDataDict import (
    LedgerBaseModelDataDict,
)


class PFindingClassificationChoiceDescriptorDataDict(LedgerBaseModelDataDict):
    patient_finding_classification_choice: str
    classification_choice_descriptor: str
    descriptor_value: Union[str, int, float, bool, List[str]]
