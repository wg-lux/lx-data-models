from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypedDict, Union

from .Indication import Indication
from .IndicationDataDict import IndicationDataDict
from .IndicationType import IndicationType
from .IndicationTypeDataDict import IndicationTypeDataDict

if TYPE_CHECKING:
    from .IndicationDjango import IndicationDjango
    from .IndicationTypeDjango import IndicationTypeDjango


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

if TYPE_CHECKING:

    class KbIndicationDjangoLookupType(TypedDict):
        Indication: type[IndicationDjango]
        IndicationType: type[IndicationTypeDjango]

    kb_indication_django_lookup: KbIndicationDjangoLookupType
    kb_indication_django_models = Union[IndicationDjango, IndicationTypeDjango]

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
    "KbIndicationDjangoLookupType",
    "kb_indication_django_models",
]


def __getattr__(name: str) -> Any:
    if name not in {
        "IndicationDjango",
        "IndicationTypeDjango",
        "KbIndicationDjangoLookupType",
        "kb_indication_django_lookup",
        "kb_indication_django_models",
    }:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    from .IndicationDjango import IndicationDjango
    from .IndicationTypeDjango import IndicationTypeDjango

    class KbIndicationDjangoLookupType(TypedDict):
        Indication: type[IndicationDjango]
        IndicationType: type[IndicationTypeDjango]

    exports = {
        "IndicationDjango": IndicationDjango,
        "IndicationTypeDjango": IndicationTypeDjango,
        "KbIndicationDjangoLookupType": KbIndicationDjangoLookupType,
        "kb_indication_django_lookup": KbIndicationDjangoLookupType(
            Indication=IndicationDjango,
            IndicationType=IndicationTypeDjango,
        ),
        "kb_indication_django_models": Union[IndicationDjango, IndicationTypeDjango],
    }
    globals().update(exports)
    return exports[name]
