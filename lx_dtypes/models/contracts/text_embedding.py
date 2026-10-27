"""Versioned text vector spaces and explicit report-span annotation requests."""

from math import hypot
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, FiniteFloat, model_validator


class EmbeddingSpace(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    model: str = Field(min_length=1, max_length=255)
    revision: str = Field(min_length=1, max_length=255)
    dimensions: int = Field(ge=1, le=16384)
    preprocessing: str = Field(min_length=1, max_length=255)


class TextEmbedding(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    space: EmbeddingSpace
    vector: list[FiniteFloat] = Field(min_length=1, max_length=16384)

    @model_validator(mode="after")
    def validate_vector(self) -> Self:
        if len(self.vector) != self.space.dimensions:
            raise ValueError("Embedding dimensions do not match the declared space")
        if not 0 < hypot(*self.vector) < float("inf"):
            raise ValueError("Embedding must have a finite nonzero norm")
        return self

    def cosine(self, other: "TextEmbedding") -> float:
        if self.space != other.space:
            raise ValueError("Cannot compare different embedding spaces")
        left, right = hypot(*self.vector), hypot(*other.vector)
        return max(
            -1.0,
            min(
                1.0,
                sum(
                    (a / left) * (b / right)
                    for a, b in zip(self.vector, other.vector, strict=True)
                ),
            ),
        )


class ReportConceptSpan(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    report_id: int = Field(gt=0)
    source_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    start: int = Field(ge=0)
    end: int = Field(gt=0)
    concept_kind: Literal["examination", "finding", "classification"]
    annotation_id: int = Field(gt=0)

    @model_validator(mode="after")
    def validate_span(self) -> Self:
        if not 0 < self.end - self.start <= 2000:
            raise ValueError("Report span must contain 1 to 2000 characters")
        return self
