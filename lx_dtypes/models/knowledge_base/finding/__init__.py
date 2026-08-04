from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypedDict, Union

from ._Finding import Finding
from ._FindingType import FindingType
from .FindingDataDict import FindingDataDict
from .FindingTypeDataDict import FindingTypeDataDict


if TYPE_CHECKING:
    from ._FindingDjango import FindingDjango
    from ._FindingTypeDjango import FindingTypeDjango


class KbFindingLookupType(TypedDict):
    Finding: type[Finding]
    FindingDataDict: type[FindingDataDict]
    FindingType: type[FindingType]
    FindingTypeDataDict: type[FindingTypeDataDict]


kb_finding_lookup = KbFindingLookupType(
    Finding=Finding,
    FindingDataDict=FindingDataDict,
    FindingType=FindingType,
    FindingTypeDataDict=FindingTypeDataDict,
)

kb_finding_models = Union[
    Finding,
    FindingType,
]

kb_finding_ddicts = Union[
    FindingDataDict,
    FindingTypeDataDict,
]

if TYPE_CHECKING:
    class KbFindingDjangoLookupType(TypedDict):
        Finding: type[FindingDjango]
        FindingType: type[FindingTypeDjango]

    kb_finding_django_lookup: KbFindingDjangoLookupType
    kb_finding_django_models = Union[
        FindingDjango,
        FindingTypeDjango,
    ]

__all__ = [
    "Finding",
    "FindingDataDict",
    "FindingType",
    "FindingTypeDataDict",
    "kb_finding_lookup",
    "KbFindingLookupType",
    "kb_finding_models",
    "kb_finding_ddicts",
    "kb_finding_django_lookup",
    "KbFindingDjangoLookupType",
    "kb_finding_django_models",
]


def __getattr__(name: str) -> Any:
    if name not in {
        "FindingDjango",
        "FindingTypeDjango",
        "KbFindingDjangoLookupType",
        "kb_finding_django_lookup",
        "kb_finding_django_models",
    }:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    from ._FindingDjango import FindingDjango
    from ._FindingTypeDjango import FindingTypeDjango

    class KbFindingDjangoLookupType(TypedDict):
        Finding: type[FindingDjango]
        FindingType: type[FindingTypeDjango]

    exports = {
        "FindingDjango": FindingDjango,
        "FindingTypeDjango": FindingTypeDjango,
        "KbFindingDjangoLookupType": KbFindingDjangoLookupType,
        "kb_finding_django_lookup": KbFindingDjangoLookupType(
            Finding=FindingDjango,
            FindingType=FindingTypeDjango,
        ),
        "kb_finding_django_models": Union[FindingDjango, FindingTypeDjango],
    }
    globals().update(exports)
    return exports[name]
