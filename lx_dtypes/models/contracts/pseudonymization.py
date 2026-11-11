from __future__ import annotations

from typing import Literal

from pydantic import ConfigDict, Field

from lx_dtypes.models.model import FrozenContractModel

type QuasiIdentifierField = Literal[
    "first_name",
    "last_name",
    "center",
    "gender",
    "dob_band",
]
type QuasiIdentifierSubset = tuple[QuasiIdentifierField, ...]


class KAnonymityResult(FrozenContractModel):
    k_value: int = Field(ge=0)
    is_k_anonymous: bool
    threshold: int = Field(ge=1)

    def as_tuple(self) -> tuple[int, bool]:
        return self.k_value, self.is_k_anonymous


class KPseudonymizationResult(FrozenContractModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

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
