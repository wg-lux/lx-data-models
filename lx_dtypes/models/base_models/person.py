from datetime import date
from typing import Literal, NotRequired, Optional, Union
from uuid import UUID

from pydantic import Field, field_serializer, field_validator

from lx_dtypes.utils.factories.field_defaults import str_unknown_factory, uuid_factory
from lx_dtypes.models.base_models.base_model import (
    AppBaseModelUUIDTags,
    AppBaseModelUUIDTagsDataDict,
)


class PersonDataDict(AppBaseModelUUIDTagsDataDict):
    first_name: str
    last_name: str
    dob: NotRequired[Optional[str]]
    email: NotRequired[Optional[str]]
    gender: str
    phone: NotRequired[Optional[str]]
    street: NotRequired[Optional[str]]
    city: NotRequired[Optional[str]]
    state: NotRequired[Optional[str]]
    zip_code: NotRequired[Optional[str]]
    country: NotRequired[Optional[str]]


class Person(AppBaseModelUUIDTags):
    first_name: str = Field(default_factory=str_unknown_factory)
    last_name: str = Field(default_factory=str_unknown_factory)
    uuid: str = Field(default_factory=uuid_factory)
    dob: Optional[date] = None
    email: Optional[str] = None
    gender: Literal["female", "male", "other", "unknown"] = Field(
        default_factory=str_unknown_factory
    )
    phone: Optional[str] = None
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None

    @field_validator("dob", mode="before")
    def validate_dob(cls, value: Optional[Union[str, date]]) -> Optional[date]:
        if value is None:
            return value
        if isinstance(value, date):
            return value
        return date.fromisoformat(value)

    @field_serializer("dob")
    def serialize_dob(self, dob: Optional[date]) -> Optional[str]:
        if dob is None:
            return None
        return dob.isoformat()

    @field_validator("uuid", mode="before")
    def validate_uuid(cls, value: UUID | str) -> str:
        if isinstance(value, UUID):
            return str(value)
        return value
