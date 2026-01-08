from typing import TypedDict, Union

from lx_dtypes.models.knowledge_base.citation.Citation import Citation
from lx_dtypes.models.knowledge_base.citation.CitationDataDict import CitationDataDict


class KbCitationLookupType(TypedDict):
    Citation: type[Citation]


kb_citation_lookup: KbCitationLookupType = KbCitationLookupType(
    Citation=Citation,
)

kb_citation_models = Union[Citation,]

kb_citation_ddicts = Union[CitationDataDict,]

__all__ = [
    "Citation",
    "CitationDataDict",
    "kb_citation_lookup",
    "kb_citation_models",
    "kb_citation_ddicts",
]
