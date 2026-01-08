from __future__ import annotations

import uuid as uuid_module
from typing import Any, ClassVar, Dict, Generic, List, Literal, Self, TypeVar, Union

from django.db import models

from lx_dtypes.models.base.app_base_model.django.AppBaseModelDjango import (
    AppBaseModelDjango,
)
from lx_dtypes.utils.django_field_types import (
    CharFieldType,
    OptionalCharFieldType,
    UUIDFieldType,
)

DDictT = TypeVar("DDictT")

# TODO Move to a common location
GENDER_OPTIONS_LITERAL = Literal["female", "male", "other", "unknown"]
GENDER_CHOICES: Dict[GENDER_OPTIONS_LITERAL, str] = {
    "female": "Female",
    "male": "Male",
    "other": "Other",
    "unknown": "Unknown",
}
AppBaseModelDjango


class AppBaseModelUUIDTagsDjango(AppBaseModelDjango):
    """Abstract base model with name and UUID fields."""

    uuid: UUIDFieldType = models.UUIDField(
        default=uuid_module.uuid4, editable=False, unique=True, primary_key=True
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
    ) -> Dict[str, Any]:  # TODO Change when we have proper ManyToMany field for tags
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


class AppBaseModelNamesUUIDTagsDjango(AppBaseModelUUIDTagsDjango):
    """Abstract base model with name and UUID fields."""

    name: CharFieldType = models.CharField(max_length=255, unique=True)
    name_de: OptionalCharFieldType = models.CharField(
        max_length=255, null=True, blank=True
    )
    name_en: OptionalCharFieldType = models.CharField(
        max_length=255, null=True, blank=True
    )
    description: OptionalCharFieldType = models.CharField(
        max_length=1024, null=True, blank=True
    )

    class Meta(AppBaseModelUUIDTagsDjango.Meta):
        abstract = True


class KnowledgebaseBaseModel(AppBaseModelNamesUUIDTagsDjango, Generic[DDictT]):
    """Abstract base model with UUID field."""

    objects: ClassVar[models.Manager[Self]]  # type: ignore[misc]

    kb_module_name: CharFieldType = models.CharField(
        max_length=255,
        default="unknown",
    )

    class Meta(AppBaseModelNamesUUIDTagsDjango.Meta):
        abstract = True

    @property
    def ddict_class(self) -> type[DDictT]:
        """Return the DataDict type associated with this model."""
        raise NotImplementedError("Subclasses must implement ddict_class")

    @classmethod
    def list_type_fields(cls) -> List[str]:
        """Return a list of fields that are lists in the DataDict."""
        raise NotImplementedError("Subclasses must implement list_type_fields")

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

    @classmethod
    def get_by_name(cls, name: str) -> Self:
        """Get a model instance by its name.

        Args:
            name (str): The name of the model instance.

        Returns:
            KnowledgebaseBaseModel: The model instance with the given name.
        """
        instance = cls.objects.get(name=name)
        return instance
