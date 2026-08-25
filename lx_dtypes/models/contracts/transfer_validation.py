from __future__ import annotations

from typing import cast

from pydantic import BaseModel, ConfigDict, Field

type TransferValidationLogScalar = str | int | float | bool | None
type TransferValidationLogValue = (
    TransferValidationLogScalar
    | list["TransferValidationLogValue"]
    | dict[str, "TransferValidationLogValue"]
)


class TransferValidationFailureLogPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    error_fields: list[str] = Field(default_factory=list)
    request_method: str
    remote_addr_sha256: str | None = None
    transfer_key_sha256: str | None = None
    transfer_job_id: str | None = None
    resource_kind: str | None = None


def dump_transfer_validation_failure_log_payload(
    payload: TransferValidationFailureLogPayload,
) -> dict[str, TransferValidationLogValue]:
    return cast(
        dict[str, TransferValidationLogValue], payload.model_dump(mode="python")
    )


__all__ = [
    "TransferValidationFailureLogPayload",
    "TransferValidationLogScalar",
    "TransferValidationLogValue",
    "dump_transfer_validation_failure_log_payload",
]
