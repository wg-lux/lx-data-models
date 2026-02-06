from typing import TypeVar

from pydantic import Field

from lx_dtypes.factories import str_unknown_factory

from .AppBaseModelNamesUUIDTags import (
    AppBaseModelNamesUUIDTags,
)
from .InterfaceMixIns import (
    DDictMixIn,
    ListFieldSerializationMixIn,
)

DDictT = TypeVar("DDictT")


class KnowledgebaseBaseModel(
    ListFieldSerializationMixIn,
    AppBaseModelNamesUUIDTags,
    DDictMixIn[DDictT],
    # Generic[DDictT],
):
    kb_module_name: str = Field(default_factory=str_unknown_factory)
