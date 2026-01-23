import uuid as uuid_module
from typing import Any, Dict, List, Self, Union

from django.db import models

from lx_dtypes.models.base.app_base_model.django.AppBaseModelDjango import (
    AppBaseModelDjango,
)
from lx_dtypes.utils.django_field_types import CharFieldType, UUIDFieldType


class AppBaseModelUUIDTagsDjango(AppBaseModelDjango):
    """Abstract base model with name and UUID fields."""

    # Default: UUID is the primary key
    uuid: UUIDFieldType = models.UUIDField(
        default=uuid_module.uuid4,
        editable=False,
        unique=True,
        primary_key=True,
    )
    tags: CharFieldType = models.CharField(max_length=1024, blank=True)

    @classmethod
    def str_list_to_list(cls, value: Union[str, List[str], None]) -> List[str]:
        """
        Normalize an input that may be None, a list, or a delimited string into a list of cleaned tag strings.

        Parameters:
            value (Union[str, List[str], None]): The input to normalize. May be:
                - None, which yields an empty list.
                - A list of values, whose items will be converted to strings and trimmed.
                - A string containing comma-separated tokens and/or surrounding brackets/quotes (e.g. "a,b", "['a','b']"), which will be split on commas and trimmed.

        Returns:
            List[str]: A list of non-empty strings with surrounding whitespace and surrounding single/double quotes removed.
        """
        if value is None:
            return []
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]

        text = str(value).strip()
        if not text:
            return []

        tokens = text.strip("[]")
        items: List[str] = []
        for token in tokens.split(","):
            cleaned = token.strip().strip("'\"")
            if cleaned:
                items.append(cleaned)
        return items

    def _to_ddict(
        self,
    ) -> Dict[str, Any]:  # TODO DEPRECATED?
        """
        Produce a serializable representation of the instance with normalized tags and a stringified uuid.

        Returns:
            data (Dict[str, Any]): Mapping of the instance fields where `tags` is a list of tag strings
            (empty list if no tags) and `uuid` is converted to its string form.
        """
        data = super()._to_ddict()
        # replace "[" and "]" from tags string to convert it to list
        tags = data.get("tags", "")
        if tags:
            assert isinstance(tags, str)
            tags = self.str_list_to_list(tags)
        else:
            tags = []
        data["tags"] = tags

        data["uuid"] = str(data["uuid"])
        return data

    class Meta(AppBaseModelDjango.Meta):
        abstract = True

    @classmethod
    def get_by_uuid(cls, uuid: Union[str, uuid_module.UUID]) -> Self:
        """
        Retrieve the model instance identified by the given UUID.

        Parameters:
            uuid (str | uuid.UUID): UUID value identifying the instance; string UUIDs will be converted to `uuid.UUID`.

        Returns:
            Self: The model instance with the given UUID.
        """
        if isinstance(uuid, str):
            uuid = uuid_module.UUID(uuid)
        instance = cls.objects.get(uuid=uuid)
        return instance
