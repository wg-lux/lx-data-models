from __future__ import annotations

import uuid as uuid_module
from typing import Any, ClassVar, Dict

from django.db import models

from .typing import (
    DateTimeField,
    OptionalCharFieldType,
    OptionalDateFieldType,
    OptionalEmailFieldType,
    UUIDFieldType,
)

GENDER_CHOICES = {
    "female": "Female",
    "male": "Male",
    "other": "Other",
    "unknown": "Unknown",
}


class AppBaseModel(models.Model):
    """Abstract base model with common fields."""

    created_at: ClassVar[DateTimeField] = models.DateTimeField(auto_now_add=True)

    class Meta:
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


class PersonModel(AppBaseModel):
    uuid: ClassVar[UUIDFieldType] = models.UUIDField(
        default=uuid_module.uuid4, editable=False, unique=True
    )
    first_name: ClassVar[OptionalCharFieldType] = models.CharField(
        max_length=150, null=True, blank=True
    )
    last_name: ClassVar[OptionalCharFieldType] = models.CharField(max_length=150)
    dob: ClassVar[OptionalDateFieldType] = models.DateField(null=True, blank=True)

    email: ClassVar[OptionalEmailFieldType] = models.EmailField(
        max_length=254, null=True, blank=True
    )

    gender: ClassVar[OptionalCharFieldType] = models.CharField(
        max_length=50, null=True, blank=True, choices=GENDER_CHOICES
    )

    phone: ClassVar[OptionalCharFieldType] = models.CharField(
        max_length=50, null=True, blank=True
    )
    street: ClassVar[OptionalCharFieldType] = models.CharField(
        max_length=255, null=True, blank=True
    )
    city: ClassVar[OptionalCharFieldType] = models.CharField(
        max_length=100, null=True, blank=True
    )
    state: ClassVar[OptionalCharFieldType] = models.CharField(
        max_length=100, null=True, blank=True
    )
    zip_code: ClassVar[OptionalCharFieldType] = models.CharField(
        max_length=20, null=True, blank=True
    )
    country: ClassVar[OptionalCharFieldType] = models.CharField(
        max_length=100, null=True, blank=True
    )

    class Meta(AppBaseModel.Meta):
        abstract = True
