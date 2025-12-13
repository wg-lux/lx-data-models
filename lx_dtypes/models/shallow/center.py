from typing import List

from pydantic import Field

from lx_dtypes.utils.factories.field_defaults import list_of_str_factory, uuid_factory
from lx_dtypes.utils.mixins.base_model import BaseModelMixin
from lx_dtypes.utils.mixins.tags import TaggedMixin


class CenterShallow(BaseModelMixin, TaggedMixin):
    """Center shallow model."""

    uuid: str = Field(default_factory=uuid_factory)
    examiner_uuids: List[str] = Field(default_factory=list_of_str_factory)
