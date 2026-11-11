from __future__ import annotations

from pydantic import Field

from lx_dtypes.models.model import FrozenContractModel


class PatientExaminationPatientDataPayload(FrozenContractModel):
    id: int = Field(ge=1)
    first_name: str = Field(min_length=1)
    last_name: str = Field(min_length=1)


__all__ = ["PatientExaminationPatientDataPayload"]
