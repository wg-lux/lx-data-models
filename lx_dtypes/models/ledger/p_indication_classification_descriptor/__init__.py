from typing import TypedDict, Union

from .DataDict import PIndicationClassificationDescriptorDataDict
from .Django import PIndicationClassificationDescriptorDjango
from .Pydantic import PIndicationClassificationDescriptor


class LPIndicationClassificationDescriptorDjangoLookupType(TypedDict):
    PIndicationClassificationDescriptor: type[
        PIndicationClassificationDescriptorDjango
    ]


l_p_indication_classification_descriptor_django_lookup = (
    LPIndicationClassificationDescriptorDjangoLookupType(
        PIndicationClassificationDescriptor=PIndicationClassificationDescriptorDjango,
    )
)


class LPIndicationClassificationDescriptorLookupType(TypedDict):
    PIndicationClassificationDescriptor: type[PIndicationClassificationDescriptor]
    PIndicationClassificationDescriptorDataDict: type[
        PIndicationClassificationDescriptorDataDict
    ]


l_p_indication_classification_descriptor_lookup = (
    LPIndicationClassificationDescriptorLookupType(
        PIndicationClassificationDescriptor=PIndicationClassificationDescriptor,
        PIndicationClassificationDescriptorDataDict=(
            PIndicationClassificationDescriptorDataDict
        ),
    )
)
l_p_indication_classification_descriptor_models = Union[
    PIndicationClassificationDescriptor,
]
l_p_indication_classification_descriptor_ddicts = Union[
    PIndicationClassificationDescriptorDataDict,
]
l_p_indication_classification_descriptor_django_models = Union[
    PIndicationClassificationDescriptorDjango,
]

__all__ = [
    "PIndicationClassificationDescriptor",
    "PIndicationClassificationDescriptorDataDict",
    "l_p_indication_classification_descriptor_django_models",
    "l_p_indication_classification_descriptor_django_lookup",
    "LPIndicationClassificationDescriptorDjangoLookupType",
    "l_p_indication_classification_descriptor_lookup",
    "LPIndicationClassificationDescriptorLookupType",
    "l_p_indication_classification_descriptor_models",
    "l_p_indication_classification_descriptor_ddicts",
]
