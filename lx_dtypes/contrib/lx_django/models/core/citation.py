from django.db import models

from lx_dtypes.models.core.citation import (
    CitationDataDict,
)
from lx_dtypes.models.core.citation_shallow import (
    CitationShallowDataDict,
)

from ..base_model.base_model import KnowledgeBaseModel
from ..typing import (
    CharFieldType,
    IntegerFieldType,
    JSONFieldType,
    OptionalCharFieldType,
)


class Citation(KnowledgeBaseModel):
    """Model representing a Citation."""

    citation_key: CharFieldType = models.CharField(max_length=255, unique=True)
    title: CharFieldType = models.CharField(max_length=1024)
    abstract: OptionalCharFieldType = models.CharField(
        max_length=5000, null=True, blank=True
    )
    authors: CharFieldType = models.CharField(
        max_length=2000, blank=True
    )  # store as comma-separated names
    publication_year: IntegerFieldType = models.IntegerField(null=True, blank=True)
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

    @property
    def ddict_shallow(self) -> type[CitationShallowDataDict]:
        return CitationShallowDataDict

    @property
    def ddict(self) -> type[CitationDataDict]:
        return CitationDataDict

    def to_ddict_shallow(self) -> CitationShallowDataDict:
        """Convert the Citation model instance to a CitationShallowDataDict.

        Returns:
            CitationShallowDataDict: The converted data dictionary.
        """
        data_dict = self._to_ddict()
        data_dict["authors"] = self.str_list_to_list(self.authors)
        data_dict["keywords"] = self.str_list_to_list(self.keywords)

        ddict = self.ddict_shallow(**data_dict)
        return ddict
