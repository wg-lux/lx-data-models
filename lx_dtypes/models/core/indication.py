from typing import Dict

from pydantic import Field

from lx_dtypes.models.shallow.indication import IndicationShallow, IndicationTypeShallow
from lx_dtypes.utils.factories.field_defaults import indication_type_by_name_factory


class IndicationType(IndicationTypeShallow):
    """Model representing an indication type."""

    pass


class Indication(IndicationShallow):
    """Model representing an indication."""

    types: Dict[str, IndicationType] = Field(default_factory=indication_type_by_name_factory)
