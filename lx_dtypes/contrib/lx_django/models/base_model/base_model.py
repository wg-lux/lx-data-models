from __future__ import annotations

import uuid as uuid_module
from typing import Any, ClassVar, Dict, List, Union

from django.db import models

from ..typing import CharFieldType, DateTimeField, OptionalCharFieldType, UUIDFieldType

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


class AppBaseModelUUIDTags(AppBaseModel):
    """Abstract base model with name and UUID fields."""

    uuid: UUIDFieldType = models.UUIDField(
        default=uuid_module.uuid4, editable=False, unique=True
    )
    tags: CharFieldType = models.CharField(max_length=1024, blank=True)

    def str_list_to_list(self, value: Union[str, List[str], None]) -> List[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]

        text = str(value).strip()
        if not text:
            return []

        tokens = text.strip("[]")
        items: List[str] = []
        for token in tokens.split(","):
            cleaned = token.strip().strip("'\"")
            if cleaned:
                items.append(cleaned)
        return items

    def _to_ddict(
        self,
    ) -> Dict[str, Any]:  # TODO Change when we have proper ManyToMany field for tags
        data = super()._to_ddict()
        # replace "[" and "]" from tags string to convert it to list
        tags = data.get("tags", "")
        if tags:
            assert isinstance(tags, str)
            tags = self.str_list_to_list(tags)
        else:
            tags = []
        data["tags"] = tags

        data["uuid"] = str(data["uuid"])
        return data

    class Meta(AppBaseModel.Meta):
        abstract = True


class AppBaseModelNamesUUIDTags(AppBaseModelUUIDTags):
    """Abstract base model with name and UUID fields."""

    name: CharFieldType = models.CharField(max_length=255)
    name_de: OptionalCharFieldType = models.CharField(
        max_length=255, null=True, blank=True
    )
    name_en: OptionalCharFieldType = models.CharField(
        max_length=255, null=True, blank=True
    )
    description: OptionalCharFieldType = models.CharField(
        max_length=1024, null=True, blank=True
    )

    class Meta(AppBaseModelUUIDTags.Meta):
        abstract = True
