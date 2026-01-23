from typing import TypedDict, Union

from .Indication import Indication
from .IndicationDataDict import IndicationDataDict
from .IndicationDjango import IndicationDjango
from .IndicationType import IndicationType
from .IndicationTypeDataDict import IndicationTypeDataDict
from .IndicationTypeDjango import IndicationTypeDjango


class KbIndicationDjangoLookupType(TypedDict):
    Indication: type[IndicationDjango]
    IndicationType: type[IndicationTypeDjango]


kb_indication_django_lookup = KbIndicationDjangoLookupType(
    Indication=IndicationDjango,
    IndicationType=IndicationTypeDjango,
)


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

kb_indication_django_models = Union[
    IndicationDjango,
    IndicationTypeDjango,
]

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
    "kb_indication_django_lookup",
]
