from lx_dtypes.models.base.app_base_model.ddict.AppBaseModelUUIDTagsDataDict import (
    AppBaseModelUUIDTagsDataDict,
)


class LedgerBaseModelDataDict(AppBaseModelUUIDTagsDataDict):
    external_ids: dict[str, str]
