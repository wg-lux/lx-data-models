from datetime import date
from typing import Literal, Optional

from pydantic import Field

from lx_dtypes.utils.factories.field_defaults import str_unknown_factory, uuid_factory
from lx_dtypes.utils.mixins.base_model import AppBaseModel


class Person(AppBaseModel):
    first_name: str
    last_name: str
    uuid: str = Field(default_factory=uuid_factory)
    dob: Optional[date] = None
    email: Optional[str] = None
    gender: Literal["female", "male", "other", "unknown"] = str_unknown_factory()
    phone: Optional[str] = None
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None
