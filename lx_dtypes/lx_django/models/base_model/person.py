from __future__ import annotations

from django.db import models

from ..typing import (
    OptionalCharFieldType,
    OptionalDateFieldType,
    OptionalEmailFieldType,
)
from .base_model import AppBaseModelUUIDTags

GENDER_CHOICES = {
    "female": "Female",
    "male": "Male",
    "other": "Other",
    "unknown": "Unknown",
}


class PersonModel(AppBaseModelUUIDTags):
    first_name: OptionalCharFieldType = models.CharField(
        max_length=150, null=True, blank=True
    )
    last_name: OptionalCharFieldType = models.CharField(
        max_length=150, null=True, blank=True
    )
    dob: OptionalDateFieldType = models.DateField(null=True, blank=True)
    email: OptionalEmailFieldType = models.EmailField(
        max_length=254, null=True, blank=True
    )

    gender: OptionalCharFieldType = models.CharField(
        max_length=50, null=True, blank=True, choices=GENDER_CHOICES
    )

    phone: OptionalCharFieldType = models.CharField(
        max_length=50, null=True, blank=True
    )
    street: OptionalCharFieldType = models.CharField(
        max_length=255, null=True, blank=True
    )
    city: OptionalCharFieldType = models.CharField(
        max_length=100, null=True, blank=True
    )
    state: OptionalCharFieldType = models.CharField(
        max_length=100, null=True, blank=True
    )
    zip_code: OptionalCharFieldType = models.CharField(
        max_length=20, null=True, blank=True
    )
    country: OptionalCharFieldType = models.CharField(
        max_length=100, null=True, blank=True
    )

    class Meta(AppBaseModelUUIDTags.Meta):
        abstract = True
