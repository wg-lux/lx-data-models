from typing import TypedDict, Union

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

from .InformationSourceDjango import InformationSourceDjango
from .InformationSourceTypeDjango import InformationSourceTypeDjango


class KbInformationSourceDjangoLookupType(TypedDict):
    InformationSource: type[InformationSourceDjango]
    InformationSourceType: type[InformationSourceTypeDjango]


kb_information_source_django_lookup = KbInformationSourceDjangoLookupType(
    InformationSource=InformationSourceDjango,
    InformationSourceType=InformationSourceTypeDjango,
)


class KbInformationSourceLookupType(TypedDict):
    InformationSource: type[InformationSource]
    InformationSourceType: type[InformationSourceType]


kb_information_source_lookup = KbInformationSourceLookupType(
    InformationSource=InformationSource, InformationSourceType=InformationSourceType
)

kb_information_source_models = Union[InformationSource, InformationSourceType]
kb_information_source_ddicts = Union[
    InformationSourceDataDict, InformationSourceTypeDataDict
]
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
