from datetime import date
from typing import Optional

from pydantic import Field

from lx_dtypes.factories.literals import str_unknown_factory
from lx_dtypes.models.base.app_base_model.pydantic.AppBaseModel import AppBaseModel
from lx_dtypes.names import GENDER_OPTIONS_LITERAL


class Person(AppBaseModel):
    first_name: str = Field(default_factory=str_unknown_factory)
    last_name: str = Field(default_factory=str_unknown_factory)
    dob: Optional[date] = None
    email: Optional[str] = None
    gender: GENDER_OPTIONS_LITERAL = Field(default_factory=str_unknown_factory)
    phone: Optional[str] = None
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None
