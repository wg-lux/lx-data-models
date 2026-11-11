from __future__ import annotations

from pydantic import ConfigDict

from lx_dtypes.models.model import DtypesModel


class SensitiveMetaUpdatePayload(DtypesModel):
    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    dob_verified: bool = False
    names_verified: bool = False
    center_name: str = ""
    patient_gender_name: str = ""
    patient_first_name: str = ""
    patient_last_name: str = ""


__all__ = ["SensitiveMetaUpdatePayload"]
