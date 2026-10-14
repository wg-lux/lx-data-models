from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import TypedDict

from pydantic import BaseModel, ConfigDict, Field

type JsonNull = None
type SensitiveMetaRepairValue = str | date


class SensitiveMetaPatientRepairData(TypedDict, total=False):
    patient_first_name: str
    patient_last_name: str
    patient_dob: date
    examination_date: date
    center_name: str


class SensitiveMetaPatientRepairCreatePayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    patient_first_name: str = Field(default="Patient", min_length=1)
    patient_last_name: str = Field(default="Unknown", min_length=1)
    patient_dob: date = Field(default=date(1990, 1, 1))
    examination_date: date
    center_name: str = Field(min_length=1)


class SensitiveMetaPatientRepairUpdatePayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)

    patient_first_name: str | JsonNull = None
    patient_last_name: str | JsonNull = None
    patient_dob: date | JsonNull = None
    examination_date: date | JsonNull = None


class VideoPathRepairFileInfoPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    absolute_path: Path
    relative_path: Path
    size_mb: float = Field(ge=0.0)


type VideoPathRepairFileIndex = dict[str, VideoPathRepairFileInfoPayload]


def dump_sensitive_meta_patient_repair_create_payload(
    payload: SensitiveMetaPatientRepairCreatePayload,
) -> SensitiveMetaPatientRepairData:
    return {
        "patient_first_name": payload.patient_first_name,
        "patient_last_name": payload.patient_last_name,
        "patient_dob": payload.patient_dob,
        "examination_date": payload.examination_date,
        "center_name": payload.center_name,
    }


def dump_sensitive_meta_patient_repair_update_payload(
    payload: SensitiveMetaPatientRepairUpdatePayload,
) -> SensitiveMetaPatientRepairData:
    data: SensitiveMetaPatientRepairData = {}
    if payload.patient_first_name is not None:
        data["patient_first_name"] = payload.patient_first_name
    if payload.patient_last_name is not None:
        data["patient_last_name"] = payload.patient_last_name
    if payload.patient_dob is not None:
        data["patient_dob"] = payload.patient_dob
    if payload.examination_date is not None:
        data["examination_date"] = payload.examination_date
    return data


__all__ = [
    "SensitiveMetaPatientRepairCreatePayload",
    "SensitiveMetaPatientRepairData",
    "SensitiveMetaPatientRepairUpdatePayload",
    "SensitiveMetaRepairValue",
    "VideoPathRepairFileIndex",
    "VideoPathRepairFileInfoPayload",
    "dump_sensitive_meta_patient_repair_create_payload",
    "dump_sensitive_meta_patient_repair_update_payload",
]
