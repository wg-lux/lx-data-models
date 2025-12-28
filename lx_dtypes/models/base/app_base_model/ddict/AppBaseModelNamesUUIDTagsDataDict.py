from lx_dtypes.models.base.app_base_model.ddict.AppBaseModelUUIDTagsDataDict import (
    AppBaseModelUUIDTagsDataDict,
)


class AppBaseModelNamesUUIDTagsDataDict(AppBaseModelUUIDTagsDataDict):
    """
    Data dictionary for application base models with names, UUIDs, and tags.

    Fields:
    - name: str
    - name_de: str
    - name_en: str
    - description: str
    """

    name: str
    name_de: str
    name_en: str
    description: str
