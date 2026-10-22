from datetime import date

import pytest
from pydantic import ValidationError

from lx_dtypes.models.contracts.media_workflow_policy import (
    AnonymizationValidationAcknowledgement,
    ConsentWithdrawalOutcome,
    DeletionStatus,
    ExaminationAnnotationLink,
    ExaminationLinkKey,
    LocationDeletionOutcome,
    SharedSaltMatchingPrecondition,
    WithdrawalLocation,
)

HASH = "a" * 64


def _outcomes(
    local: DeletionStatus = DeletionStatus.DELETED,
    hub: DeletionStatus = DeletionStatus.DELETED,
    frozen: DeletionStatus = DeletionStatus.DELETED,
) -> list[LocationDeletionOutcome]:
    reason = "frozen release"
    return [
        LocationDeletionOutcome(location=WithdrawalLocation.LOCAL, status=local),
        LocationDeletionOutcome(location=WithdrawalLocation.HUB, status=hub),
        LocationDeletionOutcome(
            location=WithdrawalLocation.FROZEN_DATASETS, status=frozen, reason=reason
        ),
    ]


def test_acknowledgement_must_be_confirmed() -> None:
    assert AnonymizationValidationAcknowledgement(
        confirmed_no_identifying_content_visible=True, hide_prompt_in_future=True
    ).hide_prompt_in_future
    with pytest.raises(ValidationError):
        AnonymizationValidationAcknowledgement.model_validate(
            {"confirmed_no_identifying_content_visible": False}
        )


@pytest.mark.parametrize("value", ["", "A" * 64, "a" * 63, "g" * 64])
def test_examination_key_requires_lowercase_sha256(value: str) -> None:
    with pytest.raises(ValidationError):
        ExaminationLinkKey(sensitive_meta_hash=value, examination_date=date(2026, 1, 2))


def test_annotation_link_requires_positive_ids() -> None:
    key = ExaminationLinkKey(
        sensitive_meta_hash=HASH, examination_date=date(2026, 1, 2)
    )
    assert ExaminationAnnotationLink(key=key, video_id=1, report_id=2).report_id == 2
    with pytest.raises(ValidationError):
        ExaminationAnnotationLink(key=key, video_id=0, report_id=2)


def test_hub_matching_needs_equal_salt_generation() -> None:
    SharedSaltMatchingPrecondition(
        local_salt_fingerprint="fingerprint-1", hub_salt_fingerprint="fingerprint-1"
    )
    with pytest.raises(ValidationError, match="salt"):
        SharedSaltMatchingPrecondition(
            local_salt_fingerprint="fingerprint-1", hub_salt_fingerprint="fingerprint-2"
        )


def test_impossible_deletion_needs_reason() -> None:
    with pytest.raises(ValidationError, match="why"):
        LocationDeletionOutcome(
            location=WithdrawalLocation.HUB, status=DeletionStatus.NOT_POSSIBLE
        )


def test_withdrawal_must_cover_each_location_once() -> None:
    outcomes = _outcomes()
    assert ConsentWithdrawalOutcome(outcomes=tuple(outcomes)).local_erased
    with pytest.raises(ValidationError):
        ConsentWithdrawalOutcome(outcomes=tuple(outcomes[:2]))
    with pytest.raises(ValidationError):
        ConsentWithdrawalOutcome(outcomes=(*outcomes, outcomes[0]))


def test_pending_local_deletion_is_not_erased() -> None:
    outcome = ConsentWithdrawalOutcome(
        outcomes=tuple(_outcomes(local=DeletionStatus.PENDING))
    )
    assert not outcome.local_erased
