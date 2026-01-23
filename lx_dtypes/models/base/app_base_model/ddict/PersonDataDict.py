from typing import Optional, TypedDict

from lx_dtypes.names import GENDER_OPTIONS_LITERAL


class PersonDataDict(TypedDict):
    first_name: str
    last_name: str
    dob: Optional[str]
    email: Optional[str]
    gender: GENDER_OPTIONS_LITERAL
    phone: Optional[str]
    street: Optional[str]
    city: Optional[str]
    state: Optional[str]
    zip_code: Optional[str]
    country: Optional[str]
