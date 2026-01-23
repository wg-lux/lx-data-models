import uuid as uuid_module
from typing import ClassVar, Generic, List, Literal, Self, TypeVar

from django.db import models

from lx_dtypes.models.base.app_base_model.django.AppBaseModelUUIDTagsDjango import (
    AppBaseModelUUIDTagsDjango,
)
from lx_dtypes.names import mk_lbm_list_type_fields
from lx_dtypes.serialization import parse_str_list
from lx_dtypes.utils.django_field_types import JSONFieldType, UUIDFieldType
from lx_dtypes.utils.django_sync import parse_list_type_field, sync_from_ddict_m2m_field

DDictT = TypeVar("DDictT")


class LedgerBaseModelDjango(
    AppBaseModelUUIDTagsDjango,
    Generic[DDictT],
):
    """Abstract base model with UUID field."""

    uuid: UUIDFieldType = models.UUIDField(
        default=uuid_module.uuid4,
        editable=False,
        unique=True,
        db_index=True,
        primary_key=True,
    )
    external_ids: JSONFieldType = models.JSONField(default=dict)

    objects: ClassVar[models.Manager[Self]]  # type: ignore[misc]

    class Meta(AppBaseModelUUIDTagsDjango.Meta):
        abstract = True

    @classmethod
    def m2m_fields(cls) -> List[str]:
        """
        Return many-to-many field names excluding nested data-dictionary fields.

        Filters the list of m2m fields inherited from the superclass by removing any fields listed in this class's nested_fields().

        Returns:
            List[str]: Many-to-many field names that are not nested.
        """
        m2m_fields = super().m2m_fields()
        nested_fields = cls.nested_fields()
        return [field for field in m2m_fields if field not in nested_fields]

    @classmethod
    def fk_fields(cls) -> List[str]:
        """
        List foreign-key field names excluding any fields declared as nested DataDict fields.

        Returns:
            List[str]: Foreign-key field names from the superclass with nested fields removed.
        """
        fk_fields = super().fk_fields()
        nested_fields = cls.nested_fields()
        return [field for field in fk_fields if field not in nested_fields]

    @classmethod
    def nested_fields(cls) -> List[str]:
        """
        List nested DataDict field names for the model.

        Returns:
            List[str]: Field names that should be treated as nested DataDicts (empty by default).
        """
        default_nested_fields: List[str] = []
        return default_nested_fields

    @classmethod
    def ddict_pk_field_name(cls) -> Literal["uuid"]:
        """
        Primary key field name used in the DataDict.

        Returns:
            The string "uuid", the primary key field name used in the DataDict.
        """
        return "uuid"

    @classmethod
    def list_type_fields(cls) -> List[str]:
        """
        Identify the model field names that should be treated as lists in the DataDict.

        Returns:
            List[str]: Field names that represent list-type values in the DataDict.
        """
        default_list_type_fields = mk_lbm_list_type_fields()
        return default_list_type_fields

    @property
    def ddict_class(self) -> type[DDictT]:
        """
        The DataDict class associated with this model. Subclasses must implement this property.

        Returns:
            type[DDictT]: The DataDict type used to construct ddict instances for this model.
        """
        raise NotImplementedError("Subclasses must implement ddict_class")

    @property
    def ddict(self) -> DDictT:
        """
        Create a DataDict instance representing the model's current data.

        Builds a mapping from the model to the DataDict by expanding nested relations into nested ddict structures, representing many-to-many fields as lists of related primary keys, resolving foreign keys to the related object's primary-key string or `None`, parsing list-type fields, and omitting fields with `None` values. Ensures `created_at` is present if the model has it and removes an `id` key if present.

        Returns:
            DDictT: An instance of the model's associated DataDict class populated from the model.
        """

        fields = tuple(self.ddict_class.__annotations__.keys())  # type: ignore
        data: dict = {}  # type: ignore
        m2m_field_names = set(self.m2m_fields())
        list_fields = set(self.list_type_fields())
        nested_fields = set(self.nested_fields())
        pk_field_name = self.ddict_pk_field_name()
        fk_fields = set(self.fk_fields())
        for field in fields:
            if field in nested_fields:
                print(f"Processing nested field: {field}")
                # Nested objects are handled separately; skip here to avoid missing reverse attrs
                value = getattr(self, field)

                if hasattr(value, "all"):
                    value = [_.ddict for _ in value.all()]  # type: ignore
                else:
                    value = value.ddict  # type: ignore

            elif field in m2m_field_names:
                related_names = list(
                    getattr(self, field).values_list(pk_field_name, flat=True)
                )
                value = related_names

            elif field in fk_fields:
                related_obj = getattr(self, field)
                related_model = type(related_obj)
                related_pk_field_name = related_model.ddict_pk_field_name()  # type: ignore
                if related_obj is not None:
                    value = getattr(related_obj, related_pk_field_name)
                    value = str(value)
                else:
                    value = None

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
    def sync_from_ddict(cls, defaults: DDictT) -> Self:
        """
        Create or update a model instance from a DataDict and synchronize related fields.

        This classmethod applies values from `defaults` to the model: it ignores nested-data fields, resolves and assigns foreign-key relations based on the related objects' pk, parses list-type fields, and sets many-to-many relations after the instance is created or updated. The resulting instance is refreshed from the database before being returned.

        Parameters:
            defaults (DDictT): DataDict containing field values to apply; may include fk identifiers and m2m lists.

        Returns:
            Self: The created or updated model instance with relations synchronized.
        """

        nested_fields = cls.nested_fields()
        for field in nested_fields:
            if field in defaults:  # type: ignore
                defaults.pop(field)  # type: ignore

        pk_field_name = cls.ddict_pk_field_name()
        # Split m2m values out so they can be set after the instance is saved.
        defaults_dict = dict(defaults)  # type: ignore
        m2m_field_names = set(cls.m2m_fields())
        m2m_values: dict[str, object] = {}
        fk_field_names = set(cls.fk_fields())
        fk_values: dict[str, object] = {}

        # Ensure no m2m field stays in defaults passed to update_or_create
        for field in m2m_field_names:
            if field in defaults_dict:
                m2m_values[field] = defaults_dict.pop(field)

        # fk_fields in defaults contain related object names or uuids; extract them
        # replace with actual related object in defaults_dict
        for field in fk_field_names:
            if field in defaults_dict:
                related_name = defaults_dict.pop(field)
                fk_values[field] = related_name
                # get or create the related object
                field_obj = cls._meta.get_field(field)  # type: ignore
                related_model = field_obj.related_model  # type: ignore
                target_pk_field = related_model.ddict_pk_field_name()  # type: ignore
                related_obj = related_model.objects.get(  # type: ignore
                    **{target_pk_field: related_name}
                )  # type: ignore
                defaults_dict[field] = related_obj  # type: ignore

        instance, _created = cls.objects.update_or_create(
            pk=defaults_dict[pk_field_name],  # type: ignore
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
