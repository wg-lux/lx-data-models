from typing import TypedDict, Union

from .Finding import Finding
from .FindingDataDict import FindingDataDict
from .FindingType import FindingType
from .FindingTypeDataDict import FindingTypeDataDict


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

__all__ = [
    "Finding",
    "FindingDataDict",
    "FindingType",
    "FindingTypeDataDict",
    "kb_finding_lookup",
    "KbFindingLookupType",
    "kb_finding_models",
    "kb_finding_ddicts",
]
