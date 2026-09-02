from __future__ import annotations

import base64
import hashlib
import json
import re
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

type HubMediaEnvelopeContractVersion = Literal["hub_media_envelope_v1"]
type HubMediaEnvelopeProfile = Literal["x25519-hkdf-sha256-aes256gcm-v1"]
type HubMediaResourceKind = Literal["video", "report"]
type HubMediaRole = Literal["processed"]
type HubMediaTransferMode = Literal["metadata_and_processed_media"]

_SHA256_PATTERN = r"^[0-9a-f]{64}$"
_IDENTIFIER_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9._:-]*$"
_BASE64URL_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")


class _StrictFrozenContract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


def _canonical_json_bytes(value: dict[str, object]) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _encode_base64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _validate_base64url(value: str, *, expected_size: int, field_name: str) -> str:
    if not _BASE64URL_PATTERN.fullmatch(value):
        raise ValueError(f"{field_name} must be unpadded base64url")
    try:
        decoded = base64.b64decode(
            value + "=" * (-len(value) % 4),
            altchars=b"-_",
            validate=True,
        )
    except (ValueError, TypeError) as exc:
        raise ValueError(f"{field_name} must be unpadded base64url") from exc
    if len(decoded) != expected_size:
        raise ValueError(f"{field_name} must decode to {expected_size} bytes")
    if _encode_base64url(decoded) != value:
        raise ValueError(f"{field_name} must use canonical unpadded base64url")
    return value


class HubMediaEnvelopeMetadata(_StrictFrozenContract):
    """Authenticated metadata for one processed-media Hub transfer."""

    contract_version: HubMediaEnvelopeContractVersion = "hub_media_envelope_v1"
    profile: HubMediaEnvelopeProfile = "x25519-hkdf-sha256-aes256gcm-v1"
    transfer_key: str = Field(
        min_length=1,
        max_length=255,
        pattern=_IDENTIFIER_PATTERN,
    )
    source_node_key: str = Field(
        min_length=1,
        max_length=253,
        pattern=_IDENTIFIER_PATTERN,
    )
    source_center_key: str = Field(
        min_length=1,
        max_length=255,
        pattern=_IDENTIFIER_PATTERN,
    )
    target_node_key: str = Field(
        min_length=1,
        max_length=253,
        pattern=_IDENTIFIER_PATTERN,
    )
    resource_kind: HubMediaResourceKind
    resource_hash: str = Field(min_length=1, max_length=255, pattern=r"^\S+$")
    processed_media_hash: str = Field(pattern=_SHA256_PATTERN)
    transfer_mode: HubMediaTransferMode = "metadata_and_processed_media"
    media_role: HubMediaRole = "processed"
    plaintext_sha256: str = Field(pattern=_SHA256_PATTERN)
    plaintext_size: int = Field(gt=0)
    recipient_key_id: str = Field(pattern=_SHA256_PATTERN)
    ephemeral_public_key: str
    wrap_salt: str
    wrap_nonce: str
    wrapped_data_encryption_key: str
    payload_nonce: str
    payload_tag: str

    @field_validator("ephemeral_public_key")
    @classmethod
    def _validate_ephemeral_public_key(cls, value: str) -> str:
        return _validate_base64url(
            value,
            expected_size=32,
            field_name="ephemeral_public_key",
        )

    @field_validator("wrap_salt")
    @classmethod
    def _validate_wrap_salt(cls, value: str) -> str:
        return _validate_base64url(value, expected_size=16, field_name="wrap_salt")

    @field_validator("wrap_nonce", "payload_nonce")
    @classmethod
    def _validate_nonce(cls, value: str, info: object) -> str:
        field_name = str(getattr(info, "field_name", "nonce"))
        return _validate_base64url(value, expected_size=12, field_name=field_name)

    @field_validator("wrapped_data_encryption_key")
    @classmethod
    def _validate_wrapped_data_encryption_key(cls, value: str) -> str:
        return _validate_base64url(
            value,
            expected_size=48,
            field_name="wrapped_data_encryption_key",
        )

    @field_validator("payload_tag")
    @classmethod
    def _validate_payload_tag(cls, value: str) -> str:
        return _validate_base64url(value, expected_size=16, field_name="payload_tag")

    @model_validator(mode="after")
    def _validate_processed_media_digest(self) -> Self:
        if self.processed_media_hash != self.plaintext_sha256:
            raise ValueError(
                "processed_media_hash must match plaintext_sha256 for processed media"
            )
        return self

    def authenticated_data(self) -> bytes:
        """Return canonical additional authenticated data for key and media AEAD."""

        return _canonical_json_bytes(
            {
                "contract_version": self.contract_version,
                "ephemeral_public_key": self.ephemeral_public_key,
                "media_role": self.media_role,
                "payload_nonce": self.payload_nonce,
                "plaintext_sha256": self.plaintext_sha256,
                "plaintext_size": self.plaintext_size,
                "processed_media_hash": self.processed_media_hash,
                "profile": self.profile,
                "recipient_key_id": self.recipient_key_id,
                "resource_hash": self.resource_hash,
                "resource_kind": self.resource_kind,
                "source_center_key": self.source_center_key,
                "source_node_key": self.source_node_key,
                "target_node_key": self.target_node_key,
                "transfer_key": self.transfer_key,
                "transfer_mode": self.transfer_mode,
                "wrap_nonce": self.wrap_nonce,
                "wrap_salt": self.wrap_salt,
            }
        )

    def envelope_fingerprint_sha256(self) -> str:
        """Identify the complete immutable envelope, including its AEAD outputs."""

        serialized = _canonical_json_bytes(self.model_dump(mode="json"))
        return hashlib.sha256(serialized).hexdigest()


class HubMediaEnvelopeReceipt(_StrictFrozenContract):
    """Verified-apply acknowledgement bound to one exact media envelope."""

    contract_version: Literal["hub_media_envelope_receipt_v1"] = (
        "hub_media_envelope_receipt_v1"
    )
    envelope_contract_version: HubMediaEnvelopeContractVersion = "hub_media_envelope_v1"
    profile: HubMediaEnvelopeProfile = "x25519-hkdf-sha256-aes256gcm-v1"
    transfer_key: str = Field(
        min_length=1,
        max_length=255,
        pattern=_IDENTIFIER_PATTERN,
    )
    source_node_key: str = Field(
        min_length=1,
        max_length=253,
        pattern=_IDENTIFIER_PATTERN,
    )
    source_center_key: str = Field(
        min_length=1,
        max_length=255,
        pattern=_IDENTIFIER_PATTERN,
    )
    target_node_key: str = Field(
        min_length=1,
        max_length=253,
        pattern=_IDENTIFIER_PATTERN,
    )
    resource_kind: HubMediaResourceKind
    resource_hash: str = Field(min_length=1, max_length=255, pattern=r"^\S+$")
    processed_media_hash: str = Field(pattern=_SHA256_PATTERN)
    transfer_mode: HubMediaTransferMode = "metadata_and_processed_media"
    media_role: HubMediaRole = "processed"
    plaintext_sha256: str = Field(pattern=_SHA256_PATTERN)
    plaintext_size: int = Field(gt=0)
    recipient_key_id: str = Field(pattern=_SHA256_PATTERN)
    ciphertext_sha256: str = Field(pattern=_SHA256_PATTERN)
    ciphertext_size: int = Field(gt=0)
    envelope_fingerprint_sha256: str = Field(pattern=_SHA256_PATTERN)
    receiver_transfer_id: str = Field(min_length=1, max_length=255)
    transfer_status: Literal["applied"] = "applied"
    processing_decision: str = Field(min_length=1, max_length=64)
    verified: Literal[True] = True

    @model_validator(mode="after")
    def _validate_media_evidence(self) -> Self:
        if self.processed_media_hash != self.plaintext_sha256:
            raise ValueError(
                "processed_media_hash must match plaintext_sha256 for processed media"
            )
        if self.ciphertext_size != self.plaintext_size:
            raise ValueError(
                "ciphertext_size must match plaintext_size for the version 1 profile"
            )
        return self


def validate_hub_media_receipt_matches_envelope(
    *,
    envelope: HubMediaEnvelopeMetadata,
    receipt: HubMediaEnvelopeReceipt,
) -> HubMediaEnvelopeReceipt:
    """Reject an acknowledgement that identifies any other transfer or envelope."""

    expected: dict[str, object] = {
        "envelope_contract_version": envelope.contract_version,
        "profile": envelope.profile,
        "transfer_key": envelope.transfer_key,
        "source_node_key": envelope.source_node_key,
        "source_center_key": envelope.source_center_key,
        "target_node_key": envelope.target_node_key,
        "resource_kind": envelope.resource_kind,
        "resource_hash": envelope.resource_hash,
        "processed_media_hash": envelope.processed_media_hash,
        "transfer_mode": envelope.transfer_mode,
        "media_role": envelope.media_role,
        "plaintext_sha256": envelope.plaintext_sha256,
        "plaintext_size": envelope.plaintext_size,
        "recipient_key_id": envelope.recipient_key_id,
        "envelope_fingerprint_sha256": envelope.envelope_fingerprint_sha256(),
    }
    mismatches = [
        field_name
        for field_name, expected_value in expected.items()
        if getattr(receipt, field_name) != expected_value
    ]
    if mismatches:
        raise ValueError(
            "Hub media receipt does not match envelope fields: "
            + ", ".join(sorted(mismatches))
        )
    return receipt


__all__ = [
    "HubMediaEnvelopeContractVersion",
    "HubMediaEnvelopeMetadata",
    "HubMediaEnvelopeProfile",
    "HubMediaEnvelopeReceipt",
    "HubMediaResourceKind",
    "HubMediaRole",
    "HubMediaTransferMode",
    "validate_hub_media_receipt_matches_envelope",
]
