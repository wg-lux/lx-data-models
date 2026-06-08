from __future__ import annotations

from typing import Literal, TypeAlias

from pydantic import BaseModel, ConfigDict, Field

QuasiIdentifierField: TypeAlias = Literal[
    "first_name",
    "last_name",
    "center",
    "gender",
    "dob_band",
]
QuasiIdentifierSubset: TypeAlias = tuple[QuasiIdentifierField, ...]


class KAnonymityResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    k_value: int = Field(ge=0)
    is_k_anonymous: bool
    threshold: int = Field(ge=1)

    def as_tuple(self) -> tuple[int, bool]:
        return self.k_value, self.is_k_anonymous


class KPseudonymizationResult(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        extra="forbid",
        frozen=True,
        strict=True,
    )

    k_value_after: int = Field(ge=0)
    is_k_anonymous_after: bool
    threshold: int = Field(ge=1)

    def as_tuple(self) -> tuple[int, bool]:
        return self.k_value_after, self.is_k_anonymous_after


__all__ = [
    "KAnonymityResult",
    "KPseudonymizationResult",
    "QuasiIdentifierField",
    "QuasiIdentifierSubset",
]
