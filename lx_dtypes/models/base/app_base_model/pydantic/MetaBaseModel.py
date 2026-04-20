from typing import TypeVar

from lx_dtypes.models.base.app_base_model.pydantic import AppBaseModelUUIDTags

from .InterfaceMixIns import (
    DDictMixIn,
    ListFieldSerializationMixIn,
)

DDictT = TypeVar("DDictT")


class MetaBaseModel(
    ListFieldSerializationMixIn,
    AppBaseModelUUIDTags,
    DDictMixIn[DDictT],
):
    pass
