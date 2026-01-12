from typing import List

from lx_dtypes.models.base.app_base_model.ddict.LedgerBaseModelDataDict import (
    LedgerBaseModelDataDict,
)


class CenterDataDict(LedgerBaseModelDataDict):
    examiners: List[str]
