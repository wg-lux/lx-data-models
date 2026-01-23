from typing import TypedDict, Union

from lx_dtypes.models.knowledge_base.citation.Citation import Citation
from lx_dtypes.models.knowledge_base.citation.CitationDataDict import CitationDataDict
from lx_dtypes.models.knowledge_base.citation.CitationDjango import CitationDjango


class KbCitationLookupType(TypedDict):
    Citation: type[Citation]


kb_citation_lookup: KbCitationLookupType = KbCitationLookupType(
    Citation=Citation,
)


class KbCitationDjangoLookupType(TypedDict):
    Citation: type[CitationDjango]


kb_citation_django_lookup = KbCitationDjangoLookupType(
    Citation=CitationDjango,
)

kb_citation_models = Union[Citation,]

kb_citation_ddicts = Union[CitationDataDict,]

kb_citation_django_models = Union[CitationDjango,]

__all__ = [
    "Citation",
    "CitationDataDict",
    "kb_citation_lookup",
    "kb_citation_models",
    "kb_citation_ddicts",
    "kb_citation_django_models",
    "CitationDjango",
    "kb_citation_django_lookup",
    "KbCitationDjangoLookupType",
]
