import uuid as uuid_module
from typing import ClassVar, Generic, List, Self, TypeVar, Union

from django.db import models

from lx_dtypes.models.base.app_base_model.django.AppBaseModelNamesUUIDTagsDjango import (
    AppBaseModelNamesUUIDTagsDjango,
)
from lx_dtypes.names import mk_kbbm_list_type_fields
from lx_dtypes.serialization import parse_str_list
from lx_dtypes.utils.django_field_types import CharFieldType, UUIDFieldType

DDictT = TypeVar("DDictT")


class KnowledgebaseBaseModelDjango(AppBaseModelNamesUUIDTagsDjango, Generic[DDictT]):
    """Abstract base model with UUID field."""

    # Override: keep uuid as unique, indexed, non-PK; use name as PK for KB models
    uuid: UUIDFieldType = models.UUIDField(
        default=uuid_module.uuid4,
        editable=False,
        unique=True,
        db_index=True,
        primary_key=False,
    )

    name: CharFieldType = models.CharField(
        max_length=255,
        unique=True,
        primary_key=True,
    )

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

        # Split m2m values out so they can be set after the instance is saved.
        defaults_dict = dict(defaults)  # type: ignore
        m2m_field_names = set(cls.m2m_fields())
        m2m_values: dict[str, object] = {}

        # Ensure no m2m field stays in defaults passed to update_or_create
        for field in m2m_field_names:
            if field in defaults_dict:
                m2m_values[field] = defaults_dict.pop(field)

        instance, _created = cls.objects.update_or_create(
            name=defaults_dict["name"],  # type: ignore
            defaults=defaults_dict,  # type: ignore
        )

        # list type fields need special handling, as they are provided as comma separated strings
        # Skip many-to-many fields here; they are handled separately below via .set().
        for field_name in cls.list_type_fields():
            if field_name in m2m_field_names:
                continue
            if field_name in defaults_dict:
                value = getattr(instance, field_name)
                if isinstance(value, str):
                    value = [
                        item.strip()
                        for item in value.strip("[]").split(",")
                        if item.strip()
                    ]
                setattr(instance, field_name, value)

        # # Set many-to-many relations after creation/update.
        if m2m_values:
            for field_name, related_names in m2m_values.items():
                if related_names is None:
                    continue

                # Normalize to a list of identifiers
                if isinstance(related_names, str):
                    related_iterable = [related_names]
                elif isinstance(related_names, (list, tuple, set)):
                    related_iterable = list(related_names)
                else:
                    related_iterable = [related_names]  # type: ignore

                field = cls._meta.get_field(field_name)  # type: ignore
                related_model = field.related_model  # type: ignore

                related_instances = []
                for related_name in related_iterable:
                    related_obj, _ = related_model.objects.get_or_create(  # type: ignore[attr-defined]
                        name=related_name
                    )
                    related_instances.append(related_obj)

                # Use the manager to set M2M relations; avoids direct assignment errors
                getattr(instance, field_name).set(related_instances)

        instance.refresh_from_db()

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
        m2m_field_names = set(self.m2m_fields())
        list_fields = set(self.list_type_fields())
        for field in fields:
            if field in m2m_field_names:
                related_names = list(
                    getattr(self, field).values_list("name", flat=True)
                )
                value = related_names
                # value = (
                #     parse_str_list(related_names)
                #     if field in list_fields
                #     else related_names
                # )
            elif field in list_fields:
                raw_value = getattr(self, field)
                value = parse_str_list(raw_value)
            else:
                value = getattr(self, field)
            if value is not None:
                data[field] = value
        # Align with pydantic model dump which includes created_at
        if "created_at" not in data and hasattr(self, "created_at"):
            data["created_at"] = getattr(self, "created_at")
        if "id" in data:
            del data["id"]
        return self.ddict_class(**data)  # type: ignore

    @classmethod
    def list_type_fields(cls) -> List[str]:
        """Return a list of fields that are lists in the DataDict."""
        default_list_type_fields = mk_kbbm_list_type_fields()
        return default_list_type_fields

    @classmethod
    def m2m_fields(cls) -> List[str]:
        """Return a list of fields that are foreign keys in the DataDict."""

        return [field.name for field in cls._meta.get_fields() if field.many_to_many]

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
