from __future__ import annotations

import base64
import json
from typing import cast

import pytest
from pydantic import ValidationError

from lx_dtypes.models.contracts.hub_media_envelope import (
    HubMediaEnvelopeMetadata,
    HubMediaEnvelopeReceipt,
    validate_hub_media_receipt_matches_envelope,
)

_DIGEST_A = "a" * 64
_DIGEST_B = "b" * 64
_DIGEST_C = "c" * 64


def _b64url(size: int, value: int) -> str:
    return base64.urlsafe_b64encode(bytes([value]) * size).rstrip(b"=").decode()


def _envelope_payload() -> dict[str, object]:
    return {
        "contract_version": "hub_media_envelope_v1",
        "profile": "x25519-hkdf-sha256-aes256gcm-v1",
        "transfer_key": "site-a__video__resource-a__processed_v1",
        "source_node_key": "site-a",
        "source_center_key": "center-a",
        "target_node_key": "hub-a",
        "resource_kind": "video",
        "resource_hash": "resource-a",
        "processed_media_hash": _DIGEST_A,
        "transfer_mode": "metadata_and_processed_media",
        "media_role": "processed",
        "plaintext_sha256": _DIGEST_A,
        "plaintext_size": 4096,
        "recipient_key_id": _DIGEST_B,
        "ephemeral_public_key": _b64url(32, 1),
        "wrap_salt": _b64url(16, 2),
        "wrap_nonce": _b64url(12, 3),
        "wrapped_data_encryption_key": _b64url(48, 4),
        "payload_nonce": _b64url(12, 5),
        "payload_tag": _b64url(16, 6),
    }


def _receipt_payload(envelope: HubMediaEnvelopeMetadata) -> dict[str, object]:
    return {
        "contract_version": "hub_media_envelope_receipt_v1",
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
        "ciphertext_sha256": _DIGEST_C,
        "ciphertext_size": envelope.plaintext_size,
        "envelope_fingerprint_sha256": envelope.envelope_fingerprint_sha256(),
        "receiver_transfer_id": "f339b08d-2356-4187-a2d0-81851a1b1436",
        "transfer_status": "applied",
        "processing_decision": "skip_processing_preserved_state",
        "verified": True,
    }


def test_envelope_accepts_complete_processed_media_identity() -> None:
    envelope = HubMediaEnvelopeMetadata.model_validate(_envelope_payload())

    assert envelope.resource_kind == "video"
    assert envelope.media_role == "processed"
    assert len(envelope.authenticated_data()) > 0


def test_envelope_is_frozen_and_forbids_unknown_fields() -> None:
    envelope = HubMediaEnvelopeMetadata.model_validate(_envelope_payload())

    with pytest.raises(ValidationError, match="frozen"):
        envelope.transfer_key = "replacement"  # type: ignore[misc]

    payload = _envelope_payload()
    payload["unexpected"] = "value"
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        HubMediaEnvelopeMetadata.model_validate(payload)


@pytest.mark.parametrize(
    "field_name",
    [
        "transfer_key",
        "source_node_key",
        "source_center_key",
        "target_node_key",
        "resource_hash",
    ],
)
def test_envelope_rejects_blank_identity(field_name: str) -> None:
    payload = _envelope_payload()
    payload[field_name] = ""

    with pytest.raises(ValidationError):
        HubMediaEnvelopeMetadata.model_validate(payload)


@pytest.mark.parametrize(
    ("field_name", "encoded_value", "error_match"),
    [
        ("ephemeral_public_key", _b64url(31, 1), "32 bytes"),
        ("wrap_salt", _b64url(15, 2), "16 bytes"),
        ("wrap_nonce", _b64url(11, 3), "12 bytes"),
        ("wrapped_data_encryption_key", _b64url(47, 4), "48 bytes"),
        ("payload_nonce", _b64url(13, 5), "12 bytes"),
        ("payload_tag", _b64url(15, 6), "16 bytes"),
        ("payload_tag", _b64url(16, 6) + "=", "unpadded base64url"),
    ],
)
def test_envelope_rejects_invalid_cryptographic_field_size_or_encoding(
    field_name: str,
    encoded_value: str,
    error_match: str,
) -> None:
    payload = _envelope_payload()
    payload[field_name] = encoded_value

    with pytest.raises(ValidationError, match=error_match):
        HubMediaEnvelopeMetadata.model_validate(payload)


def test_envelope_rejects_processed_digest_mismatch() -> None:
    payload = _envelope_payload()
    payload["plaintext_sha256"] = _DIGEST_C

    with pytest.raises(ValidationError, match="must match plaintext_sha256"):
        HubMediaEnvelopeMetadata.model_validate(payload)


def test_authenticated_data_is_canonical_and_binds_wrap_nonce() -> None:
    envelope = HubMediaEnvelopeMetadata.model_validate(_envelope_payload())
    round_tripped = HubMediaEnvelopeMetadata.model_validate_json(
        envelope.model_dump_json()
    )
    changed_payload = _envelope_payload()
    changed_payload["wrap_nonce"] = _b64url(12, 9)
    changed = HubMediaEnvelopeMetadata.model_validate(changed_payload)

    assert round_tripped.authenticated_data() == envelope.authenticated_data()
    assert (
        json.loads(envelope.authenticated_data())["wrap_nonce"] == envelope.wrap_nonce
    )
    assert changed.authenticated_data() != envelope.authenticated_data()


@pytest.mark.parametrize(
    "field_name",
    [
        "transfer_key",
        "source_node_key",
        "source_center_key",
        "target_node_key",
        "resource_kind",
        "resource_hash",
        "processed_media_hash",
        "transfer_mode",
        "media_role",
        "plaintext_sha256",
        "plaintext_size",
        "recipient_key_id",
    ],
)
def test_authenticated_data_binds_every_transfer_identity(field_name: str) -> None:
    payload = _envelope_payload()
    original = HubMediaEnvelopeMetadata.model_validate(payload)
    replacements: dict[str, object] = {
        "transfer_key": "site-b__video__resource-a__processed_v1",
        "source_node_key": "site-b",
        "source_center_key": "center-b",
        "target_node_key": "hub-b",
        "resource_kind": "report",
        "resource_hash": "resource-b",
        "processed_media_hash": _DIGEST_C,
        "transfer_mode": "metadata_and_processed_media",
        "media_role": "processed",
        "plaintext_sha256": _DIGEST_C,
        "plaintext_size": 8192,
        "recipient_key_id": _DIGEST_C,
    }
    payload[field_name] = replacements[field_name]
    if field_name in {"processed_media_hash", "plaintext_sha256"}:
        payload["processed_media_hash"] = _DIGEST_C
        payload["plaintext_sha256"] = _DIGEST_C
    if field_name in {"transfer_mode", "media_role"}:
        # Literal policy fields cannot take another valid value; presence in AAD is
        # asserted directly instead of constructing an invalid contract.
        assert field_name in json.loads(original.authenticated_data())
        return
    changed = HubMediaEnvelopeMetadata.model_validate(payload)

    assert changed.authenticated_data() != original.authenticated_data()


def test_envelope_fingerprint_binds_aead_outputs_not_in_authenticated_data() -> None:
    envelope = HubMediaEnvelopeMetadata.model_validate(_envelope_payload())
    changed_payload = _envelope_payload()
    changed_payload["payload_tag"] = _b64url(16, 10)
    changed = HubMediaEnvelopeMetadata.model_validate(changed_payload)

    assert changed.authenticated_data() == envelope.authenticated_data()
    assert (
        changed.envelope_fingerprint_sha256() != envelope.envelope_fingerprint_sha256()
    )


def test_receipt_accepts_verified_apply_and_matches_exact_envelope() -> None:
    envelope = HubMediaEnvelopeMetadata.model_validate(_envelope_payload())
    receipt = HubMediaEnvelopeReceipt.model_validate(_receipt_payload(envelope))

    assert (
        validate_hub_media_receipt_matches_envelope(
            envelope=envelope,
            receipt=receipt,
        )
        is receipt
    )


@pytest.mark.parametrize(
    ("field_name", "replacement"),
    [
        ("transfer_key", "site-b__video__resource-a__processed_v1"),
        ("source_node_key", "site-b"),
        ("source_center_key", "center-b"),
        ("target_node_key", "hub-b"),
        ("resource_kind", "report"),
        ("resource_hash", "resource-b"),
        ("recipient_key_id", _DIGEST_C),
        ("envelope_fingerprint_sha256", _DIGEST_C),
    ],
)
def test_receipt_match_rejects_each_substituted_identity(
    field_name: str,
    replacement: object,
) -> None:
    envelope = HubMediaEnvelopeMetadata.model_validate(_envelope_payload())
    payload = _receipt_payload(envelope)
    payload[field_name] = replacement
    receipt = HubMediaEnvelopeReceipt.model_validate(payload)

    with pytest.raises(ValueError, match=field_name):
        validate_hub_media_receipt_matches_envelope(
            envelope=envelope,
            receipt=receipt,
        )


@pytest.mark.parametrize(
    ("field_name", "replacement"),
    [
        ("transfer_status", "awaiting_media"),
        ("verified", False),
        ("ciphertext_size", 4095),
        ("ciphertext_sha256", "A" * 64),
    ],
)
def test_receipt_rejects_unverified_or_malformed_evidence(
    field_name: str,
    replacement: object,
) -> None:
    envelope = HubMediaEnvelopeMetadata.model_validate(_envelope_payload())
    payload = _receipt_payload(envelope)
    payload[field_name] = replacement

    with pytest.raises(ValidationError):
        HubMediaEnvelopeReceipt.model_validate(payload)


def test_models_reject_non_strict_integer_coercion() -> None:
    payload = _envelope_payload()
    payload["plaintext_size"] = cast(object, "4096")

    with pytest.raises(ValidationError, match="valid integer"):
        HubMediaEnvelopeMetadata.model_validate(payload)
