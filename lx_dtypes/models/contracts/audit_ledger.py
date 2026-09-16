from __future__ import annotations

import hashlib
import json
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from lx_dtypes.models.contracts.json_types import JsonObject

SHA256_HEX_PATTERN = r"^[0-9a-f]{64}$"


class AuditLedgerHashPayload(BaseModel):
    model_config = ConfigDict(frozen=True, strict=True)

    ts: str
    id: str
    uid: str | None = None
    obj: str
    act: str
    data: JsonObject = Field(default_factory=dict)
    prev: str = Field(pattern=SHA256_HEX_PATTERN)

    def canonical_json(self) -> str:
        return json.dumps(
            self.model_dump(mode="json"),
            sort_keys=True,
            separators=(",", ":"),
        )

    def sha256_hex(self) -> str:
        return hashlib.sha256(self.canonical_json().encode()).hexdigest()


class AuditLedgerEntryPayload(BaseModel):
    model_config = ConfigDict(frozen=True, strict=True)

    id: UUID
    ts: str
    user_id: str | None = None
    object_type: str
    object_pk: str
    action: str
    data: JsonObject
    prev_hash: str = Field(pattern=SHA256_HEX_PATTERN)
    hash: str = Field(pattern=SHA256_HEX_PATTERN)


class AuditLedgerIntegrityStatusPayload(BaseModel):
    model_config = ConfigDict(frozen=True, strict=True)

    status: Literal["unknown", "verified", "failed", "error"]
    verified: bool
    checked_at: str | None = None
    entry_count: int | None = None
    error: str | None = None
    source: str
    ledger_head_hash: str = Field(pattern=SHA256_HEX_PATTERN)
    last_entry_id: str | None = None
