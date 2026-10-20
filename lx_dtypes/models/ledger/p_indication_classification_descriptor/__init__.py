from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict, Union

from .DataDict import PIndicationClassificationDescriptorDataDict
from .Pydantic import PIndicationClassificationDescriptor

if TYPE_CHECKING:
    from .Django import PIndicationClassificationDescriptorDjango

    l_p_indication_classification_descriptor_django_lookup: (
        LPIndicationClassificationDescriptorDjangoLookupType
    )
    type l_p_indication_classification_descriptor_django_models = (
        PIndicationClassificationDescriptorDjango
    )


class LPIndicationClassificationDescriptorDjangoLookupType(TypedDict):
    PIndicationClassificationDescriptor: type[PIndicationClassificationDescriptorDjango]


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

__all__ = [
    "LPIndicationClassificationDescriptorDjangoLookupType",
    "LPIndicationClassificationDescriptorLookupType",
    "PIndicationClassificationDescriptor",
    "PIndicationClassificationDescriptorDataDict",
    "l_p_indication_classification_descriptor_ddicts",
    "l_p_indication_classification_descriptor_django_lookup",
    "l_p_indication_classification_descriptor_django_models",
    "l_p_indication_classification_descriptor_lookup",
    "l_p_indication_classification_descriptor_models",
]


def __getattr__(name: str) -> object:
    if name not in {
        "PIndicationClassificationDescriptorDjango",
        "l_p_indication_classification_descriptor_django_lookup",
        "l_p_indication_classification_descriptor_django_models",
    }:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    from .Django import PIndicationClassificationDescriptorDjango

    exports: dict[str, object] = {
        "PIndicationClassificationDescriptorDjango": PIndicationClassificationDescriptorDjango,
        "l_p_indication_classification_descriptor_django_lookup": LPIndicationClassificationDescriptorDjangoLookupType(
            PIndicationClassificationDescriptor=PIndicationClassificationDescriptorDjango
        ),
        "l_p_indication_classification_descriptor_django_models": PIndicationClassificationDescriptorDjango,
    }
    globals().update(exports)
    return exports[name]
