from typing import TypedDict, Union

from .DataDict import (
    PIndicationClassificationDataDict,
    SerializedPIndicationClassificationDataDict,
)
from .Django import PIndicationClassificationDjango
from .Pydantic import PIndicationClassification


class LPIndicationClassificationDjangoLookupType(TypedDict):
    PIndicationClassification: type[PIndicationClassificationDjango]


l_p_indication_classification_django_lookup = (
    LPIndicationClassificationDjangoLookupType(
        PIndicationClassification=PIndicationClassificationDjango,
    )
)


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
l_p_indication_classification_django_models = Union[PIndicationClassificationDjango]

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
