from typing import Any, ClassVar, Dict, Self

from django.db import models
from django_stubs_ext.db.models import TypedModelMeta

from lx_dtypes.utils.django_field_types import DateTimeField


class AppBaseModelDjango(models.Model):
    """Abstract base model with common fields."""

    objects: ClassVar[models.Manager[Self]]  # type: ignore[misc]
    created_at: ClassVar[DateTimeField] = models.DateTimeField(auto_now_add=True)

    class Meta(TypedModelMeta):
        abstract = True

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
