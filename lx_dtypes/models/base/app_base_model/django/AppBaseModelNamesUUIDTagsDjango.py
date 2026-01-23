from typing import Self

from django.db import models

from lx_dtypes.models.base.app_base_model.django.AppBaseModelUUIDTagsDjango import (
    AppBaseModelUUIDTagsDjango,
)
from lx_dtypes.utils.django_field_types import CharFieldType, OptionalCharFieldType


class AppBaseModelNamesUUIDTagsDjango(AppBaseModelUUIDTagsDjango):
    """Abstract base model with name and UUID fields."""

    # Name is unique and indexed by default; specific subclasses can override PK
    name: CharFieldType = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
    )
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

    @classmethod
    def get_by_name(cls, name: str) -> Self:
        """
        Retrieve a model instance with the given name.

        Parameters:
            name (str): The exact name to look up.

        Returns:
            Self: The model instance matching the provided name.
        """
        instance = cls.objects.get(name=name)
        return instance
