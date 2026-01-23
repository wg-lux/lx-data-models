from typing import Dict

from lx_dtypes.models.base.app_base_model.ddict.AppBaseModelUUIDTagsDataDict import (
    AppBaseModelUUIDTagsDataDict,
)


class LedgerBaseModelDataDict(AppBaseModelUUIDTagsDataDict):
    external_ids: Dict[str, str]
