from typing import Any, ClassVar, Dict, List, Self

from django.db import models
from django_stubs_ext.db.models import TypedModelMeta

from lx_dtypes.utils.django_field_types import DateTimeField


class AppBaseModelDjango(models.Model):
    """Abstract base model with common fields."""

    objects: ClassVar[models.Manager[Self]]  # type: ignore[misc]
    created_at: ClassVar[DateTimeField] = models.DateTimeField(auto_now_add=True)

    class Meta(TypedModelMeta):
        abstract = True
        app_label = "lx_dtypes_django"

    def _to_ddict(self) -> Dict[str, Any]:
        """Cleans the model instance data for dictionary representation.

        Returns:
            dict: Cleaned data dictionary.
        """
        data: Dict[str, Any] = {}
        for field in self._meta.fields:
            value = getattr(self, field.name)
            if value is not None:
                data[field.name] = value
        if "id" in data:
            del data["id"]
        return data

    @classmethod
    def m2m_fields(cls) -> List[str]:
        """Return a list of fields that are m2m relationships."""

        return [field.name for field in cls._meta.get_fields() if field.many_to_many]

    @classmethod
    def fk_fields(cls) -> List[str]:
        """Return a list of fields that are foreign keys in the DataDict."""
        relationships = [
            field.name for field in cls._meta.get_fields() if field.is_relation
        ]
        m2m_fields = cls.m2m_fields()
        return [field for field in relationships if field not in m2m_fields]
