from pydantic import Field

from lx_dtypes.factories import str_unknown_factory
from lx_dtypes.models.model import DtypesModel


class UnitMixin(DtypesModel):
    unit: str = Field(default_factory=str_unknown_factory)
