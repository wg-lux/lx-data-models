from django.db import models

from lx_dtypes.models.base.app_base_model.django.KnowledgebaseBaseModelDjango import (
    KnowledgebaseBaseModelDjango,
)
from lx_dtypes.models.knowledge_base.citation.CitationDataDict import (
    CitationDataDict,
)
from lx_dtypes.names import CITATION_MODEL_LIST_TYPE_FIELDS
from lx_dtypes.utils.django_field_types import (
    CharFieldType,
    JSONFieldType,
    OptionalCharFieldType,
    OptionalIntegerFieldType,
)


class CitationDjango(KnowledgebaseBaseModelDjango[CitationDataDict]):
    """
    Django model for citations in a knowledge base.
    """

    citation_key: CharFieldType = models.CharField(max_length=255, unique=True)
    title: CharFieldType = models.CharField(max_length=1024)
    abstract: OptionalCharFieldType = models.CharField(
        max_length=5000, null=True, blank=True
    )
    authors: CharFieldType = models.CharField(
        max_length=2000, blank=True
    )  # store as comma-separated names
    publication_year: OptionalIntegerFieldType = models.IntegerField(
        null=True, blank=True
    )
    publication_month: OptionalCharFieldType = models.CharField(
        max_length=20, null=True, blank=True
    )
    journal: OptionalCharFieldType = models.CharField(
        max_length=255, null=True, blank=True
    )
    publisher: OptionalCharFieldType = models.CharField(
        max_length=255, null=True, blank=True
    )
    volume: OptionalCharFieldType = models.CharField(
        max_length=50, null=True, blank=True
    )
    issue: OptionalCharFieldType = models.CharField(
        max_length=50, null=True, blank=True
    )
    pages: OptionalCharFieldType = models.CharField(
        max_length=50, null=True, blank=True
    )
    doi: OptionalCharFieldType = models.CharField(max_length=255, null=True, blank=True)
    url: OptionalCharFieldType = models.CharField(
        max_length=1024, null=True, blank=True
    )
    entry_type: OptionalCharFieldType = models.CharField(
        max_length=100, null=True, blank=True
    )
    language: OptionalCharFieldType = models.CharField(
        max_length=50, null=True, blank=True
    )
    keywords: CharFieldType = models.CharField(
        max_length=2000, blank=True
    )  # store as comma-separated keywords
    identifiers: JSONFieldType = models.JSONField(default=dict, blank=True)

    class Meta(KnowledgebaseBaseModelDjango.Meta):
        pass

    @property
    def ddict_class(self) -> type[CitationDataDict]:
        """
        Data dictionary class used by this model.

        Returns:
            The `CitationDataDict` class.
        """
        return CitationDataDict

    @classmethod
    def list_type_fields(cls) -> list[str]:
        """
        Identify model fields that represent list-valued data.

        Returns:
            list[str]: Field names in the model that should be treated as list-valued (e.g., comma-separated or JSON arrays).
        """
        return CITATION_MODEL_LIST_TYPE_FIELDS
