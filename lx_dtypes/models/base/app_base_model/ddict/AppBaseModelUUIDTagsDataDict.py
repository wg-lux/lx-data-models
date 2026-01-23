from typing import List

from lx_dtypes.models.base.app_base_model.ddict.AppBaseModelDataDict import (
    AppBaseModelDataDict,
)


class AppBaseModelUUIDTagsDataDict(AppBaseModelDataDict):
    """
    Base data dictionary for application base models with UUID and tags,
    inherits from AppBaseModelDataDict.

    Fields:
    - uuid: str
    - tags: List[str]
    """

    uuid: str
    tags: List[str]
