from typing import Dict, List

from pydantic import Field

from lx_dtypes.factories.typed_lists import list_of_str_factory
from lx_dtypes.models.base.app_base_model.pydantic.KnowledgebaseBaseModel import (
    KnowledgebaseBaseModel,
)
from lx_dtypes.models.knowledge_base.citation.CitationDataDict import CitationDataDict
from lx_dtypes.names import CITATION_MODEL_LIST_TYPE_FIELDS


class Citation(
    KnowledgebaseBaseModel[CitationDataDict],
):
    """Model for citations in a knowledge base."""

    citation_key: str
    title: str
    abstract: str | None = None
    authors: List[str] = Field(default_factory=list_of_str_factory)
    publication_year: int | None = None
    publication_month: str | None = None
    journal: str | None = None
    publisher: str | None = None
    volume: str | None = None
    issue: str | None = None
    pages: str | None = None
    doi: str | None = None
    url: str | None = None
    entry_type: str | None = None
    language: str | None = None
    keywords: List[str] = Field(default_factory=list_of_str_factory)
    identifiers: Dict[str, str] = Field(default_factory=dict)

    @classmethod
    def list_type_fields(cls) -> List[str]:
        """
        Provide the names of the model's fields that hold list values.

        Returns:
            list_type_fields (List[str]): A list of field names that are list-typed in this model.
        """
        return CITATION_MODEL_LIST_TYPE_FIELDS

    @property
    def ddict_class(self) -> type[CitationDataDict]:
        """
        Expose the data-dictionary class associated with this model.

        Returns:
            type[CitationDataDict]: The CitationDataDict class used to represent this model's underlying data dictionary.
        """
        return CitationDataDict
