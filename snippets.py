import uuid as uuid_module
from typing import List, Union

############
from pydantic import Field, field_serializer, field_validator

from lx_dtypes.factories import list_of_str_factory, str_uuid_factory
from lx_dtypes.models.base.app_base_model.pydantic.AppBaseModel import AppBaseModel
from lx_dtypes.names import FieldNames
from lx_dtypes.serialization import parse_str_list, serialize_str_list


class AppBaseModelUUIDTags(AppBaseModel):
    """Abstract base model with UUID field."""

    uuid: Union[str, uuid_module.UUID] = Field(default_factory=str_uuid_factory)

    tags: Union[str, List[str]] = Field(default_factory=list_of_str_factory)

    @field_validator(FieldNames.TAGS.value, mode="before")
    @classmethod
    def _coerce_tags(cls, value: List[str] | str | None) -> List[str]:
        """Accept comma-separated strings or lists and normalize to list[str]."""

        return parse_str_list(value)

    @field_serializer(FieldNames.TAGS.value, when_used="json")
    def _serialize_tags(self, tags: List[str]) -> str:
        """Serialize list of tags into a comma-separated string for JSON output."""

        return serialize_str_list(tags)


#####
from typing import Any, Dict, Union, List
from pydantic import Field
from lx_dtypes.factories.typed_lists import list_of_str_factory
