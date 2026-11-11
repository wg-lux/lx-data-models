"""Study identity and descriptive fields, independent of cohort selection."""

from pydantic import ConfigDict, Field

from lx_dtypes.models.model import StrictContractModel


class StudyDefinition(StrictContractModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=255)
    hypothesis: str = Field(default="", max_length=10000)
    description: str = Field(default="", max_length=10000)
