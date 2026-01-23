from typing import Dict, List

from lx_dtypes.models.base.app_base_model.ddict.KnowledgebaseBaseModelDataDict import (
    KnowledgebaseBaseModelDataDict,
)


class CitationDataDict(KnowledgebaseBaseModelDataDict):
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
