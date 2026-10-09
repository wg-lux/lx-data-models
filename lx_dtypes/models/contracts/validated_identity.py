from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from lx_dtypes.models.contracts.json_types import JsonObject

MediaType = Literal["video", "pdf"]


class ValidatedIdentityPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    source: str = Field(min_length=1)
    media_type: MediaType
    media_pk: str = Field(min_length=1)
    sensitive_meta_id: int = Field(ge=1)
    patient_hash: str | None = None
    examination_hash: str | None = None
    pseudo_patient_id: int | None = None
    pseudo_examination_id: int | None = None
    linked_patient_id: int | None = None
    linked_patient_examination_id: int | None = None
    case_resolution_status: str
    case_resolution_reason: str | None = None
    case_resolution_created: bool


def dump_validated_identity_payload(
    payload: ValidatedIdentityPayload,
) -> JsonObject:
    return payload.model_dump(mode="python")
