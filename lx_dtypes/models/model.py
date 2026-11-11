"""Shared validation policies for package-owned Pydantic models.

Unknown fields fail by default. Coercion and mutability are separate choices:
capture models may coerce values, strict contracts do not, and frozen contracts
also reject assignment. External projections/extensions must override ``extra``
explicitly; their exceptions are inventoried in docs/model-boundaries.yml.
"""

from pydantic import BaseModel, ConfigDict, RootModel


class DtypesModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class StrictContractModel(DtypesModel):
    model_config = ConfigDict(strict=True)


class FrozenContractModel(StrictContractModel):
    model_config = ConfigDict(frozen=True)


class DtypesRootModel[T](RootModel[T]):
    """Root values validate their declared type; mapping keys are data fields."""


__all__ = [
    "DtypesModel",
    "DtypesRootModel",
    "FrozenContractModel",
    "StrictContractModel",
]
