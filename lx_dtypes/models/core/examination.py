from typing import Dict

from pydantic import Field

from lx_dtypes.models.shallow.examination import ExaminationShallow, ExaminationTypeShallow

from .finding import Finding
from .indication import Indication


class ExaminationType(ExaminationTypeShallow):
    """Model representing an examination type."""

    pass


class Examination(ExaminationShallow):
    """Model representing a finding classification."""

    findings: Dict[str, "Finding"] = Field(default_factory=dict)
    types: Dict[str, ExaminationType] = Field(default_factory=dict)
    indications: Dict[str, "Indication"] = Field(default_factory=dict)
