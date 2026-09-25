from typing import TypedDict

from lx_dtypes.names import GENDER_OPTIONS_LITERAL


class PersonDataDict(TypedDict):
    first_name: str
    last_name: str
    dob: str | None
    email: str | None
    gender: GENDER_OPTIONS_LITERAL
    phone: str | None
    street: str | None
    city: str | None
    state: str | None
    zip_code: str | None
    country: str | None
