from pydantic import BaseModel, Field

from lx_dtypes.factories import str_unknown_factory


class UnitMixin(BaseModel):
    unit: str = Field(default_factory=str_unknown_factory)
