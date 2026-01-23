import uuid as uuid_module
from typing import List, Union

from pydantic import Field

from lx_dtypes.factories import list_of_str_factory, str_uuid_factory

from .AppBaseModel import AppBaseModel


class AppBaseModelUUIDTags(AppBaseModel):
    """Abstract base model with UUID field."""

    uuid: Union[str, uuid_module.UUID] = Field(default_factory=str_uuid_factory)

    tags: Union[str, List[str]] = Field(default_factory=list_of_str_factory)
