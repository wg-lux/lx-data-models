from pydantic import Field

from lx_dtypes.factories import str_unknown_factory
from lx_dtypes.models.model import DtypesModel


class TextDescriptorMixin(DtypesModel):
    text_max_length: int = Field(default_factory=lambda: 255)
    default_value_str: str = Field(default_factory=str_unknown_factory)
