import uuid as uuid_module
from typing import ClassVar, Generic, List, Self, TypeVar, Union

from django.db import models

from lx_dtypes.models.base.app_base_model.django.AppBaseModelNamesUUIDTagsDjango import (
    AppBaseModelNamesUUIDTagsDjango,
)
from lx_dtypes.utils.django_field_types import CharFieldType

DDictT = TypeVar("DDictT")


class KnowledgebaseBaseModelDjango(AppBaseModelNamesUUIDTagsDjango, Generic[DDictT]):
    """Abstract base model with UUID field."""

    objects: ClassVar[models.Manager[Self]]  # type: ignore[misc]

    kb_module_name: CharFieldType = models.CharField(
        max_length=255,
        default="unknown",
    )

    class Meta(AppBaseModelNamesUUIDTagsDjango.Meta):
        abstract = True

    @classmethod
    def sync_from_ddict(cls, defaults: DDictT) -> Self:
        """Sync the model instance from a DataDict.

        Args:
            defaults (DDictT): The DataDict to sync from.
        """
        instance, _created = cls.objects.update_or_create(
            name=defaults["name"],  # type: ignore
            defaults=defaults,  # type: ignore
        )

        # list type fields need special handling, as they are provided as comma separated strings
        for field_name in cls.list_type_fields():
            if field_name in defaults:  # type: ignore
                value = getattr(instance, field_name)
                if isinstance(value, str):
                    value = [
                        item.strip()
                        for item in value.strip("[]").split(",")
                        if item.strip()
                    ]
                setattr(instance, field_name, value)
        return instance

    @property
    def ddict_class(self) -> type[DDictT]:
        """Return the DataDict type associated with this model."""
        raise NotImplementedError("Subclasses must implement ddict_class")

    @property
    def ddict(self) -> DDictT:
        """Materialize the DataDict using the model contents."""
        fields = tuple(self.ddict_class.__annotations__.keys())  # type: ignore
        data: dict = {}  # type: ignore
        for field in fields:
            value = getattr(self, field)
            if value is not None:
                data[field] = value
        if "id" in data:
            del data["id"]
        return self.ddict_class(**data)  # type: ignore

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
