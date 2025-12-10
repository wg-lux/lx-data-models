from typing import Any, Dict, List

from pydantic import Field, model_validator

from lx_dtypes.utils.factories.field_defaults import list_of_str_factory
from lx_dtypes.utils.mixins.base_model import BaseModelMixin
from lx_dtypes.utils.mixins.tags import TaggedMixin


class CitationShallow(BaseModelMixin, TaggedMixin):
    """Shallow wrapper for citations without nested relations."""

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

    @model_validator(mode="before")
    @classmethod
    def ensure_name(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Value for ``name`` defaults to the citation key or title."""

        assert isinstance(data, dict)
        new_data = data.copy()
        if not new_data.get("name"):
            new_data["name"] = new_data.get("citation_key") or new_data.get("title")
        return new_data
