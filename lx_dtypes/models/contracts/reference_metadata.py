"""Shared legacy-compatible clinical descriptor definition contracts."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ClassificationSubcategoryDefinition(BaseModel):
    """Persisted knowledge-base definition accepted by EndoReg 0.2.9."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    choices: list[str]
    default: str | None = None
    required: bool | None = None
    probability: list[float] | None = None
    description: str | None = None

    @model_validator(mode="after")
    def validate_choice_references(self) -> "ClassificationSubcategoryDefinition":
        if not self.choices:
            raise ValueError("choices must not be empty")
        if self.default is not None and self.default not in self.choices:
            raise ValueError("default must be one of choices")
        if self.probability is not None and any(
            probability < 0.0 or probability > 1.0 for probability in self.probability
        ):
            raise ValueError("probability values must be between 0 and 1")
        return self


class ClassificationNumericalDescriptorDefinition(BaseModel):
    """Persisted numerical descriptor definition used by the YAML knowledge base."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    unit: str
    required: bool
    minimum: float | None = Field(default=None, alias="min")
    maximum: float | None = Field(default=None, alias="max")
    mean: float | None = None
    std: float | None = None
    default: float | None = None
    distribution: Literal["normal", "uniform"] | None = None
    description: str | None = None
