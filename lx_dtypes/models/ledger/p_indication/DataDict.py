from typing import TYPE_CHECKING, List

from lx_dtypes.models.base.app_base_model.ddict.LedgerBaseModelDataDict import (
    LedgerBaseModelDataDict,
)

if TYPE_CHECKING:
    from lx_dtypes.models.ledger.p_indication_classification.DataDict import (
        PIndicationClassificationDataDict,
    )


class PIndicationDataDict(LedgerBaseModelDataDict):
    indication: str
    patient_examination: str
    patient_indication_classifications: List["PIndicationClassificationDataDict"]
