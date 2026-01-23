import uuid as uuid_module
from typing import ClassVar, Generic, List, Literal, Self, TypeVar

from django.db import models

from lx_dtypes.models.base.app_base_model.django.AppBaseModelNamesUUIDTagsDjango import (
    AppBaseModelNamesUUIDTagsDjango,
)
from lx_dtypes.names import mk_kbbm_list_type_fields
from lx_dtypes.serialization import parse_str_list
from lx_dtypes.utils.django_field_types import CharFieldType, UUIDFieldType
from lx_dtypes.utils.django_sync import parse_list_type_field, sync_from_ddict_m2m_field

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
    def ddict_pk_field_name(cls) -> Literal["name"]:
        """
        Primary key field name used in the DataDict representation.

        Returns:
            str: The literal string "name", indicating which model field is used as the DataDict primary key.
        """
        return "name"

    @classmethod
    def sync_from_ddict(cls, defaults: DDictT) -> Self:
        """
        Create or update a model instance from a DataDict and synchronize its related fields.

        This method uses the DataDict's `name` field as the primary key to create or update the instance, resolves foreign-key fields by related object name, applies list-type field conversions, and sets many-to-many relations after the instance is saved. The instance is refreshed from the database before being returned.

        Parameters:
            defaults (DDictT): DataDict containing the fields to apply to the model. FK fields should contain related object names; m2m fields should contain iterables of related identifiers.

        Returns:
            Self: The created or updated model instance.
        """

        # Split m2m values out so they can be set after the instance is saved.
        defaults_dict = dict(defaults)  # type: ignore
        m2m_field_names = set(cls.m2m_fields())
        m2m_values: dict[str, object] = {}
        fk_field_names = set(cls.fk_fields())
        fk_values: dict[str, object] = {}
        pk_field_name = cls.ddict_pk_field_name()

        # Ensure no m2m field stays in defaults passed to update_or_create
        for field in m2m_field_names:
            if field in defaults_dict:
                m2m_values[field] = defaults_dict.pop(field)

        # fk_fields in defaults contain related object names; extract them
        # replace with actual related object in defaults_dict
        for field in fk_field_names:
            if field in defaults_dict:
                related_name = defaults_dict.pop(field)
                fk_values[field] = related_name
                # get or create the related object
                field_obj = cls._meta.get_field(field)  # type: ignore
                related_model = field_obj.related_model  # type: ignore
                related_obj = related_model.objects.get(  # type: ignore
                    name=related_name
                )
                defaults_dict[field] = related_obj  # type: ignore

        instance, _created = cls.objects.update_or_create(
            name=defaults_dict[pk_field_name],  # type: ignore
            defaults=defaults_dict,  # type: ignore
        )

        # list type fields need special handling, as they are provided as comma separated strings
        # Skip many-to-many fields here; they are handled separately below via .set().
        list_type_fields = cls.list_type_fields()
        parse_list_type_field(
            list_type_fields,
            m2m_field_names,
            defaults_dict,  # type: ignore
            instance,  # type: ignore
        )
        # # Set many-to-many relations after creation/update.
        if m2m_values:
            sync_from_ddict_m2m_field(m2m_values, instance, cls)

        instance.refresh_from_db()

        return instance

    @property
    def ddict_class(self) -> type[DDictT]:
        """
        Provide the DataDict class associated with this model.

        Returns:
            type[DDictT]: The DataDict class used to materialize instances of this model.

        Raises:
            NotImplementedError: If a subclass does not override this method.
        """
        raise NotImplementedError("Subclasses must implement ddict_class")

    @property
    def ddict(self) -> DDictT:
        """
        Constructs a DataDict instance populated from this model's fields.

        Many-to-many fields are serialized as lists of related objects' primary-key values (using the DataDict PK field name). Fields declared as list-type are parsed from their stored string representation. Fields with value `None` are omitted; if present, `created_at` is included and `id` is removed.

        Returns:
            An instance of the model's `ddict_class` populated with the collected field values.
        """
        fields = tuple(self.ddict_class.__annotations__.keys())  # type: ignore
        data: dict = {}  # type: ignore
        m2m_field_names = set(self.m2m_fields())
        list_fields = set(self.list_type_fields())
        pk_field_name = self.ddict_pk_field_name()
        for field in fields:
            if field in m2m_field_names:
                related_names = list(
                    getattr(self, field).values_list(pk_field_name, flat=True)
                )
                value = related_names

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
        """
        List field names that should be treated as list-types in the DataDict.

        Returns:
            list_type_fields (List[str]): Field names that represent lists in the DataDict.
        """
        default_list_type_fields = mk_kbbm_list_type_fields()
        return default_list_type_fields
