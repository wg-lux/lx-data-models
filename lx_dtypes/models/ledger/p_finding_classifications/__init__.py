from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict, Union

from .DataDict import PFindingClassificationsDataDict
from .Pydantic import PFindingClassifications

if TYPE_CHECKING:
    from .Django import PFindingClassificationsDjango

    l_p_finding_classifications_django_lookup: LPFindingClassificationsDjangoLookupType
    type l_p_finding_classifications_django_models = PFindingClassificationsDjango


class LPFindingClassificationsDjangoLookupType(TypedDict):
    PFindingClassifications: type[PFindingClassificationsDjango]


class LPFindingClassificationsLookupType(TypedDict):
    PFindingClassifications: type[PFindingClassifications]
    PFindingClassificationsDataDict: type[PFindingClassificationsDataDict]


l_p_finding_classifications_lookup = LPFindingClassificationsLookupType(
    PFindingClassifications=PFindingClassifications,
    PFindingClassificationsDataDict=PFindingClassificationsDataDict,
)
l_p_finding_classifications_models = Union[PFindingClassifications,]
l_p_finding_classifications_ddicts = Union[PFindingClassificationsDataDict,]
__all__ = [
    "LPFindingClassificationsDjangoLookupType",
    "LPFindingClassificationsLookupType",
    "PFindingClassifications",
    "PFindingClassificationsDataDict",
    "l_p_finding_classifications_ddicts",
    "l_p_finding_classifications_django_lookup",
    "l_p_finding_classifications_django_models",
    "l_p_finding_classifications_lookup",
    "l_p_finding_classifications_models",
]


def __getattr__(name: str) -> object:
    if name not in {
        "PFindingClassificationsDjango",
        "l_p_finding_classifications_django_lookup",
        "l_p_finding_classifications_django_models",
    }:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    from .Django import PFindingClassificationsDjango

    exports: dict[str, object] = {
        "PFindingClassificationsDjango": PFindingClassificationsDjango,
        "l_p_finding_classifications_django_lookup": LPFindingClassificationsDjangoLookupType(
            PFindingClassifications=PFindingClassificationsDjango
        ),
        "l_p_finding_classifications_django_models": PFindingClassificationsDjango,
    }
    globals().update(exports)
    return exports[name]
