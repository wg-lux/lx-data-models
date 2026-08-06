from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypedDict, Union

from lx_dtypes.models.knowledge_base.information_source.InformationSource import (
    InformationSource,
)
from lx_dtypes.models.knowledge_base.information_source.InformationSourceDataDict import (
    InformationSourceDataDict,
)
from lx_dtypes.models.knowledge_base.information_source.InformationSourceType import (
    InformationSourceType,
)
from lx_dtypes.models.knowledge_base.information_source.InformationSourceTypeDataDict import (
    InformationSourceTypeDataDict,
)

if TYPE_CHECKING:
    from .InformationSourceDjango import InformationSourceDjango
    from .InformationSourceTypeDjango import InformationSourceTypeDjango


class KbInformationSourceLookupType(TypedDict):
    InformationSource: type[InformationSource]
    InformationSourceDataDict: type[InformationSourceDataDict]
    InformationSourceType: type[InformationSourceType]
    InformationSourceTypeDataDict: type[InformationSourceTypeDataDict]


kb_information_source_lookup = KbInformationSourceLookupType(
    InformationSource=InformationSource,
    InformationSourceDataDict=InformationSourceDataDict,
    InformationSourceType=InformationSourceType,
    InformationSourceTypeDataDict=InformationSourceTypeDataDict,
)

kb_information_source_models = Union[InformationSource, InformationSourceType]
kb_information_source_ddicts = Union[
    InformationSourceDataDict, InformationSourceTypeDataDict
]
if TYPE_CHECKING:

    class KbInformationSourceDjangoLookupType(TypedDict):
        InformationSource: type[InformationSourceDjango]
        InformationSourceType: type[InformationSourceTypeDjango]

    kb_information_source_django_lookup: KbInformationSourceDjangoLookupType
    kb_information_source_django_models = Union[
        InformationSourceDjango, InformationSourceTypeDjango
    ]

__all__ = [
    "InformationSource",
    "InformationSourceDataDict",
    "InformationSourceType",
    "InformationSourceTypeDataDict",
    "kb_information_source_lookup",
    "KbInformationSourceLookupType",
    "kb_information_source_models",
    "kb_information_source_ddicts",
    "kb_information_source_django_lookup",
    "KbInformationSourceDjangoLookupType",
    "kb_information_source_django_models",
]


def __getattr__(name: str) -> Any:
    if name not in {
        "InformationSourceDjango",
        "InformationSourceTypeDjango",
        "KbInformationSourceDjangoLookupType",
        "kb_information_source_django_lookup",
        "kb_information_source_django_models",
    }:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    from .InformationSourceDjango import InformationSourceDjango
    from .InformationSourceTypeDjango import InformationSourceTypeDjango

    class KbInformationSourceDjangoLookupType(TypedDict):
        InformationSource: type[InformationSourceDjango]
        InformationSourceType: type[InformationSourceTypeDjango]

    exports = {
        "InformationSourceDjango": InformationSourceDjango,
        "InformationSourceTypeDjango": InformationSourceTypeDjango,
        "KbInformationSourceDjangoLookupType": KbInformationSourceDjangoLookupType,
        "kb_information_source_django_lookup": KbInformationSourceDjangoLookupType(
            InformationSource=InformationSourceDjango,
            InformationSourceType=InformationSourceTypeDjango,
        ),
        "kb_information_source_django_models": Union[
            InformationSourceDjango, InformationSourceTypeDjango
        ],
    }
    globals().update(exports)
    return exports[name]
