from django.db import models

from lx_dtypes.models.base.app_base_model.django.AppBaseModelUUIDTagsDjango import (
    AppBaseModelUUIDTagsDjango,
)
from lx_dtypes.utils.django_field_types import CharFieldType, OptionalCharFieldType


class AppBaseModelNamesUUIDTagsDjango(AppBaseModelUUIDTagsDjango):
    """Abstract base model with name and UUID fields."""

    name: CharFieldType = models.CharField(
        max_length=255, primary_key=True
    )  # unique=True, db_index=True)
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
