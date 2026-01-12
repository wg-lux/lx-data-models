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
        """Get a model instance by its UUID.

        Args:
            uuid (Union[str, uuid.UUID]): The UUID of the model instance.

        Returns:
            KnowledgebaseBaseModel: The model instance with the given UUID.
        """
        if isinstance(uuid, str):
            uuid = uuid_module.UUID(uuid)
        instance = cls.objects.get(uuid=uuid)
        return instance
