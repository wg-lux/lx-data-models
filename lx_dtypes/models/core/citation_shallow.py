from typing import Any, Dict, List

from pydantic import Field, model_validator

from lx_dtypes.models.base_models.base_model import (
    KnowledgebaseBaseModel,
    KnowledgebaseBaseModelDataDict,
)
from lx_dtypes.utils.factories.field_defaults import list_of_str_factory


class CitationShallowDataDict(KnowledgebaseBaseModelDataDict):
    citation_key: str
    title: str
    abstract: str | None
    authors: List[str]
    publication_year: int | None
    publication_month: str | None
    journal: str | None
    publisher: str | None
    volume: str | None
    issue: str | None
    pages: str | None
    doi: str | None
    url: str | None
    entry_type: str | None
    language: str | None
    keywords: List[str]
    identifiers: Dict[str, str]


class CitationShallow(KnowledgebaseBaseModel):
    """Shallow BaseModel for citations without nested relations.
    Captures key bibliographic details and identifiers.

    Attributes:
        citation_key (str): Unique key for the citation.
        title (str): Title of the cited work.
        abstract (str | None): Abstract or summary of the work.
        authors (List[str]): List of authors of the work.
        publication_year (int | None): Year of publication.
        publication_month (str | None): Month of publication.
        journal (str | None): Journal name if applicable.
        publisher (str | None): Publisher of the work.
        volume (str | None): Volume number if applicable.
        issue (str | None): Issue number if applicable.
        pages (str | None): Page range if applicable.
        doi (str | None): Digital Object Identifier.
        url (str | None): URL to access the work online.
        entry_type (str | None): Type of citation entry (e.g., article, book).
        language (str | None): Language of the work.
        keywords (List[str]): List of keywords associated with the work.
        identifiers (Dict[str, str]): Additional identifiers (e.g., ISBN, PubMed ID).

    """

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

    @property
    def ddict_shallow(self) -> type[CitationShallowDataDict]:
        return CitationShallowDataDict

    @model_validator(mode="before")
    @classmethod
    def ensure_name(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Value for ``name`` defaults to the citation key or title."""

        assert isinstance(data, dict)
        new_data = data.copy()
        if not new_data.get("name"):
            new_data["name"] = new_data.get("citation_key") or new_data.get("title")
        return new_data

    @model_validator(mode="before")
    @classmethod
    def np_nan_to_none(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert any numpy NaN values to None."""

        import numpy as np

        assert isinstance(data, dict)
        new_data = data.copy()
        for key, value in new_data.items():
            if isinstance(value, float) and np.isnan(value):
                new_data[key] = None
        return new_data

    def to_ddict_shallow(self) -> CitationShallowDataDict:
        data_dict = self.ddict_shallow(**self.model_dump(exclude_none=False))
        return data_dict
