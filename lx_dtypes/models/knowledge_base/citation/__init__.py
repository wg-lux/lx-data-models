from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypedDict, Union

from lx_dtypes.models.knowledge_base.citation.Citation import Citation
from lx_dtypes.models.knowledge_base.citation.CitationDataDict import CitationDataDict

if TYPE_CHECKING:
    from lx_dtypes.models.knowledge_base.citation.CitationDjango import CitationDjango


class KbCitationLookupType(TypedDict):
    Citation: type[Citation]


kb_citation_lookup: KbCitationLookupType = KbCitationLookupType(
    Citation=Citation,
)


kb_citation_models = Union[Citation,]

kb_citation_ddicts = Union[CitationDataDict,]

if TYPE_CHECKING:

    class KbCitationDjangoLookupType(TypedDict):
        Citation: type[CitationDjango]

    kb_citation_django_lookup: KbCitationDjangoLookupType
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


def __getattr__(name: str) -> Any:
    if name not in {
        "CitationDjango",
        "KbCitationDjangoLookupType",
        "kb_citation_django_lookup",
        "kb_citation_django_models",
    }:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    from lx_dtypes.models.knowledge_base.citation.CitationDjango import CitationDjango

    class KbCitationDjangoLookupType(TypedDict):
        Citation: type[CitationDjango]

    exports = {
        "CitationDjango": CitationDjango,
        "KbCitationDjangoLookupType": KbCitationDjangoLookupType,
        "kb_citation_django_lookup": KbCitationDjangoLookupType(
            Citation=CitationDjango
        ),
        "kb_citation_django_models": Union[CitationDjango,],
    }
    globals().update(exports)
    return exports[name]
