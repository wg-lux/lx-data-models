from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict, Union

from .DataDict import (
    PIndicationClassificationDataDict,
    SerializedPIndicationClassificationDataDict,
)
from .Pydantic import PIndicationClassification

if TYPE_CHECKING:
    from .Django import PIndicationClassificationDjango

    l_p_indication_classification_django_lookup: (
        LPIndicationClassificationDjangoLookupType
    )
    type l_p_indication_classification_django_models = PIndicationClassificationDjango


class LPIndicationClassificationDjangoLookupType(TypedDict):
    PIndicationClassification: type[PIndicationClassificationDjango]


class LPIndicationClassificationLookupType(TypedDict):
    PIndicationClassification: type[PIndicationClassification]
    PIndicationClassificationDataDict: type[PIndicationClassificationDataDict]
    SerializedPIndicationClassificationDataDict: type[
        SerializedPIndicationClassificationDataDict
    ]


l_p_indication_classification_lookup = LPIndicationClassificationLookupType(
    PIndicationClassification=PIndicationClassification,
    PIndicationClassificationDataDict=PIndicationClassificationDataDict,
    SerializedPIndicationClassificationDataDict=(
        SerializedPIndicationClassificationDataDict
    ),
)
l_p_indication_classification_models = Union[PIndicationClassification]
l_p_indication_classification_ddicts = Union[
    PIndicationClassificationDataDict,
    SerializedPIndicationClassificationDataDict,
]

__all__ = [
    "LPIndicationClassificationDjangoLookupType",
    "LPIndicationClassificationLookupType",
    "PIndicationClassification",
    "PIndicationClassificationDataDict",
    "SerializedPIndicationClassificationDataDict",
    "l_p_indication_classification_ddicts",
    "l_p_indication_classification_django_lookup",
    "l_p_indication_classification_django_models",
    "l_p_indication_classification_lookup",
    "l_p_indication_classification_models",
]


def __getattr__(name: str) -> object:
    if name not in {
        "PIndicationClassificationDjango",
        "l_p_indication_classification_django_lookup",
        "l_p_indication_classification_django_models",
    }:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    from .Django import PIndicationClassificationDjango

    exports: dict[str, object] = {
        "PIndicationClassificationDjango": PIndicationClassificationDjango,
        "l_p_indication_classification_django_lookup": LPIndicationClassificationDjangoLookupType(
            PIndicationClassification=PIndicationClassificationDjango
        ),
        "l_p_indication_classification_django_models": PIndicationClassificationDjango,
    }
    globals().update(exports)
    return exports[name]
