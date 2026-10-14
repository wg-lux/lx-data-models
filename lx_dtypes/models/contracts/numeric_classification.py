"""Versioned numeric interpretation without changing the source observation."""

from __future__ import annotations

from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .knowledge_base import KnowledgeBaseIdentity

FiniteNumber = Annotated[float, Field(strict=True, allow_inf_nan=False)]
Name = Annotated[str, Field(min_length=1)]


class _StrictModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        strict=True,
        frozen=True,
        str_strip_whitespace=True,
        validate_default=True,
    )


class NumericMeasurement(_StrictModel):
    """A source value with its original identity, unit and descriptor binding."""

    observation_id: Name
    source_knowledge_base: KnowledgeBaseIdentity
    descriptor: Name
    value: FiniteNumber
    unit: Name


class NumericClassificationRule(_StrictModel):
    choice: Name
    lower: FiniteNumber
    upper: FiniteNumber | None
    lower_inclusive: bool
    upper_inclusive: bool

    @model_validator(mode="after")
    def validate_interval(self) -> Self:
        if self.upper is not None and self.upper <= self.lower:
            raise ValueError("upper must exceed lower")
        if self.upper is None and self.upper_inclusive:
            raise ValueError("an unbounded upper endpoint cannot be inclusive")
        return self

    def contains(self, value: float) -> bool:
        above = value >= self.lower if self.lower_inclusive else value > self.lower
        below = self.upper is None or (
            value <= self.upper if self.upper_inclusive else value < self.upper
        )
        return above and below


class NumericClassificationRules(_StrictModel):
    """An ordered, gap-free partition from a finite lower bound to infinity."""

    schema_version: Literal[1]
    knowledge_base: KnowledgeBaseIdentity
    classification: Name
    input_descriptor: Name
    unit: Name
    resolution: Literal["continuous", "whole_number"]
    source: Name
    rules: tuple[NumericClassificationRule, ...] = Field(min_length=1)

    @field_validator("rules", mode="before")
    @classmethod
    def accept_yaml_sequence(cls, value: object) -> object:
        return tuple(value) if isinstance(value, list) else value

    @model_validator(mode="after")
    def validate_partition(self) -> Self:
        if len({rule.choice for rule in self.rules}) != len(self.rules):
            raise ValueError("choice names must be unique")
        for left, right in zip(self.rules, self.rules[1:]):
            if left.upper != right.lower:
                raise ValueError("rules must be ordered without gaps or overlaps")
            if left.upper_inclusive == right.lower_inclusive:
                raise ValueError("each shared endpoint must belong to exactly one rule")
        if self.rules[-1].upper is not None:
            raise ValueError("the last rule must have an unbounded upper endpoint")
        return self


class NumericClassificationResult(_StrictModel):
    """Derived interpretation; source KB identity is deliberately preserved."""

    measurement: NumericMeasurement
    knowledge_base: KnowledgeBaseIdentity
    classification: Name
    choice: Name
    rules_sha256: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]


__all__ = [
    "NumericClassificationResult",
    "NumericClassificationRule",
    "NumericClassificationRules",
    "NumericMeasurement",
]
