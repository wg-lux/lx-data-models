from typing import Optional

from lx_dtypes.models.base.app_base_model.ddict.AppBaseModelUUIDTagsDataDict import (
    AppBaseModelUUIDTagsDataDict,
)


class PersonDataDict(AppBaseModelUUIDTagsDataDict):
    first_name: str
    last_name: str
    dob: Optional[str]
    email: Optional[str]
    gender: str
    phone: Optional[str]
    street: Optional[str]
    city: Optional[str]
    state: Optional[str]
    zip_code: Optional[str]
    country: Optional[str]
