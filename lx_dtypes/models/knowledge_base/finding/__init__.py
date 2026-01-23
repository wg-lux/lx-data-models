from typing import TypedDict, Union

from ._Finding import Finding
from ._FindingDjango import FindingDjango
from ._FindingType import FindingType
from ._FindingTypeDjango import FindingTypeDjango
from .FindingDataDict import FindingDataDict
from .FindingTypeDataDict import FindingTypeDataDict


class KbFindingDjangoLookupType(TypedDict):
    Finding: type["FindingDjango"]
    FindingType: type["FindingTypeDjango"]


kb_finding_django_lookup = KbFindingDjangoLookupType(
    Finding=FindingDjango,
    FindingType=FindingTypeDjango,
)


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
