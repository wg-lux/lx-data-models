from typing import TypedDict, Union

from .Indication import Indication
from .IndicationDataDict import IndicationDataDict
from .IndicationType import IndicationType
from .IndicationTypeDataDict import IndicationTypeDataDict


class KbIndicationLookupType(TypedDict):
    Indication: type[Indication]
    IndicationDataDict: type[IndicationDataDict]
    IndicationType: type[IndicationType]
    IndicationTypeDataDict: type[IndicationTypeDataDict]


kb_indication_lookup = KbIndicationLookupType(
    Indication=Indication,
    IndicationDataDict=IndicationDataDict,
    IndicationType=IndicationType,
    IndicationTypeDataDict=IndicationTypeDataDict,
)

kb_indication_models = Union[
    Indication,
    IndicationType,
]

kb_indication_ddicts = Union[
    IndicationDataDict,
    IndicationTypeDataDict,
]

__all__ = [
    "Indication",
    "IndicationDataDict",
    "IndicationType",
    "IndicationTypeDataDict",
    "kb_indication_lookup",
    "KbIndicationLookupType",
    "kb_indication_models",
    "kb_indication_ddicts",
]
