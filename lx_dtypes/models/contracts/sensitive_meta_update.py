from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class SensitiveMetaUpdatePayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    dob_verified: bool = False
    names_verified: bool = False
    center_name: str = ""
    patient_gender_name: str = ""
    patient_first_name: str = ""
    patient_last_name: str = ""


__all__ = ["SensitiveMetaUpdatePayload"]
