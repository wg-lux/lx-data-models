from typing import List, Union

from lx_dtypes.models.base.app_base_model.ddict.LedgerBaseModelDataDict import (
    LedgerBaseModelDataDict,
)


class PIndicationClassificationDescriptorDataDict(LedgerBaseModelDataDict):
    patient_indication_classification: str
    classification_choice_descriptor: str
    descriptor_value: Union[str, int, float, bool, List[str]]
