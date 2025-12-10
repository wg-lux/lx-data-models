from typing import Dict

from pydantic import Field

from lx_dtypes.models.shallow.finding import FindingShallow, FindingTypeShallow
from lx_dtypes.utils.factories.field_defaults import (
    classification_by_name_factory,
    finding_type_by_name_factory,
)

from .classification import Classification


class FindingType(FindingTypeShallow):
    """Model representing a finding type."""

    pass


class Finding(FindingShallow):
    """Model representing a finding classification."""

    classifications: Dict[str, Classification] = Field(
        default_factory=classification_by_name_factory
    )
    types: Dict[str, FindingType] = Field(default_factory=finding_type_by_name_factory)
