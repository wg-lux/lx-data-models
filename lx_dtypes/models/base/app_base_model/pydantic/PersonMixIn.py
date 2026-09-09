from datetime import date

from pydantic import Field

from lx_dtypes.factories.literals import str_unknown_factory
from lx_dtypes.models.base.app_base_model.pydantic.AppBaseModel import AppBaseModel
from lx_dtypes.names import GENDER_OPTIONS_LITERAL


class Person(AppBaseModel):
    first_name: str = Field(default_factory=str_unknown_factory)
    last_name: str = Field(default_factory=str_unknown_factory)
    dob: date | None = None
    email: str | None = None
    gender: GENDER_OPTIONS_LITERAL = Field(default_factory=str_unknown_factory)
    phone: str | None = None
    street: str | None = None
    city: str | None = None
    state: str | None = None
    zip_code: str | None = None
    country: str | None = None
